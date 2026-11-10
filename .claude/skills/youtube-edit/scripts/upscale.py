#!/usr/bin/env python3
"""4x super-resolution for low-res footage with Real-ESRGAN "general-x4v3" (SRVGGNetCompact), without PyTorch.

The .pth weights are read straight from the zip/pickle and rebuilt as an ONNX graph that runs on CPU with
onnxruntime (pip install onnx onnxruntime). Real-ESRGAN is BSD-3; weights from its GitHub releases:
  https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth
  https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-wdn-x4v3.pth
Put them in work/models/ (not committed).

  denoise: 0..1 blends the two weight sets like Real-ESRGAN's -dn option
           (0 keeps the most source texture, 1 removes the most noise and compression blocking).

Library use (compose_multi.py does this when the EDL has "upscale"):
  sr = Upscaler("work/models", denoise=0.5); big = sr(rgb_float01)   # HxWx3 -> 4Hx4Wx3
CLI test:
  python3 upscale.py in.png out.png [--denoise 0.5]
"""
import sys, zipfile
from pathlib import Path

import numpy as np

DTYPES = {"FloatStorage": np.float32, "HalfStorage": np.float16, "LongStorage": np.int64,
          "IntStorage": np.int32, "DoubleStorage": np.float64}


def load_pth(path):
    """Read a PyTorch state dict (zip format) into numpy arrays without torch and without unpickling.

    data.pkl is walked opcode by opcode (pickletools) by a tiny stack machine that only builds dicts,
    tuples, numbers, strings and tensors from the raw storages. No class from the file is ever imported
    or called, so a malicious pickle can't run code; anything unexpected raises.
    """
    import pickletools
    zf = zipfile.ZipFile(path)
    prefix = zf.namelist()[0].split("/")[0]
    raw = zf.read(f"{prefix}/data.pkl")

    class G(str):          # a GLOBAL reference, kept as a name only
        pass

    def tensor(args):
        storage, offset, size, stride = args[:4]
        _, dtype, key, _loc, _n = storage
        a = np.frombuffer(zf.read(f"{prefix}/data/{key}"), dtype=DTYPES[dtype.split(".")[-1]])
        if not size:
            return a[offset:offset + 1].reshape(()).copy()
        return np.lib.stride_tricks.as_strided(a[offset:], shape=tuple(size),
                                               strides=tuple(x * a.itemsize for x in stride)).copy()

    stack, marks, memo = [], [], {}

    def pop_mark():
        i = marks.pop()
        items = stack[i:]
        del stack[i:]
        return items

    for op, arg, _pos in pickletools.genops(raw):
        n = op.name
        if n in ("PROTO", "FRAME"):
            continue
        if n == "STOP":
            break
        if n == "MARK":
            marks.append(len(stack))
        elif n in ("EMPTY_DICT",):
            stack.append({})
        elif n == "EMPTY_LIST":
            stack.append([])
        elif n == "EMPTY_TUPLE":
            stack.append(())
        elif n in ("BINUNICODE", "SHORT_BINUNICODE", "UNICODE", "BININT", "BININT1", "BININT2",
                   "LONG1", "BINFLOAT", "SHORT_BINSTRING", "BINSTRING"):
            stack.append(arg)
        elif n == "NONE":
            stack.append(None)
        elif n in ("NEWTRUE", "NEWFALSE"):
            stack.append(n == "NEWTRUE")
        elif n == "TUPLE":
            stack.append(tuple(pop_mark()))
        elif n in ("TUPLE1", "TUPLE2", "TUPLE3"):
            k = int(n[-1])
            t = tuple(stack[-k:])
            del stack[-k:]
            stack.append(t)
        elif n == "GLOBAL":
            stack.append(G(arg.replace(" ", ".")))
        elif n == "STACK_GLOBAL":
            name, mod = stack.pop(), stack.pop()
            stack.append(G(f"{mod}.{name}"))
        elif n in ("BINPUT", "LONG_BINPUT", "PUT"):
            memo[arg] = stack[-1]
        elif n == "MEMOIZE":
            memo[len(memo)] = stack[-1]
        elif n in ("BINGET", "LONG_BINGET", "GET"):
            stack.append(memo[arg])
        elif n == "BINPERSID":
            pid = stack.pop()
            stack.append(tuple(str(x) if isinstance(x, G) else x for x in pid))
        elif n == "REDUCE":
            args, fn = stack.pop(), stack.pop()
            if fn == "collections.OrderedDict":
                stack.append({})
            elif fn == "torch._utils._rebuild_tensor_v2":
                stack.append(tensor(args))
            else:
                raise ValueError(f"refusing pickle global {fn}")
        elif n == "BUILD":
            stack.pop()                      # object state (e.g. OrderedDict metadata): not needed
        elif n == "SETITEM":
            v, k = stack.pop(), stack.pop()
            stack[-1][k] = v
        elif n == "SETITEMS":
            items = pop_mark()
            for k, v in zip(items[::2], items[1::2]):
                stack[-1][k] = v
        elif n == "APPEND":
            v = stack.pop()
            stack[-1].append(v)
        elif n == "APPENDS":
            stack[-1].extend(pop_mark())
        else:
            raise ValueError(f"unsupported pickle opcode {n}")
    d = stack[-1]
    for k in ("params_ema", "params"):
        if isinstance(d, dict) and k in d:
            return d[k]
    return d


def build_onnx(sd):
    """SRVGGNetCompact: conv-PReLU x (1 + num_conv), conv to 3*16, pixel shuffle x4, + nearest-upsampled input."""
    import onnx
    from onnx import TensorProto, helper, numpy_helper
    convs = sorted({int(k.split(".")[1]) for k in sd if k.startswith("body.") and k.endswith(".weight")})
    nodes, inits, x = [], [], "input"
    for i in convs:                                       # body.N is a conv (4-D weight) or a PReLU (1-D slope)
        w = sd[f"body.{i}.weight"]
        if w.ndim == 4:
            inits += [numpy_helper.from_array(w.astype(np.float32), f"w{i}"),
                      numpy_helper.from_array(sd[f"body.{i}.bias"].astype(np.float32), f"b{i}")]
            nodes.append(helper.make_node("Conv", [x, f"w{i}", f"b{i}"], [f"c{i}"], pads=[1, 1, 1, 1]))
            x = f"c{i}"
        else:
            inits.append(numpy_helper.from_array(w.reshape(-1, 1, 1).astype(np.float32), f"s{i}"))
            nodes.append(helper.make_node("PRelu", [x, f"s{i}"], [f"p{i}"]))
            x = f"p{i}"
    nodes.append(helper.make_node("DepthToSpace", [x], ["ps"], blocksize=4, mode="CRD"))
    inits.append(numpy_helper.from_array(np.array([1, 1, 4, 4], np.float32), "scales"))
    nodes.append(helper.make_node("Resize", ["input", "", "scales"], ["up"], mode="nearest"))
    nodes.append(helper.make_node("Add", ["ps", "up"], ["output"]))
    g = helper.make_graph(nodes, "srvgg",
                          [helper.make_tensor_value_info("input", TensorProto.FLOAT, [1, 3, None, None])],
                          [helper.make_tensor_value_info("output", TensorProto.FLOAT, [1, 3, None, None])], inits)
    m = helper.make_model(g, opset_imports=[helper.make_opsetid("", 13)])
    m.ir_version = 8
    return m.SerializeToString()


class Upscaler:
    def __init__(self, model_dir="work/models", denoise=0.5, threads=0):
        import onnxruntime as ort
        a = load_pth(Path(model_dir) / "realesr-general-x4v3.pth")
        b = load_pth(Path(model_dir) / "realesr-general-wdn-x4v3.pth")
        sd = {k: (1 - denoise) * a[k] + denoise * b[k] for k in a}
        so = ort.SessionOptions()
        if threads:
            so.intra_op_num_threads = threads
        self.sess = ort.InferenceSession(build_onnx(sd), so, providers=["CPUExecutionProvider"])

    def __call__(self, rgb):
        x = np.ascontiguousarray(rgb.transpose(2, 0, 1)[None].astype(np.float32))
        y = self.sess.run(None, {"input": x})[0][0]
        return np.clip(y.transpose(1, 2, 0), 0, 1)


if __name__ == "__main__":
    import argparse, time
    import cv2
    ap = argparse.ArgumentParser()
    ap.add_argument("inp")
    ap.add_argument("out")
    ap.add_argument("--denoise", type=float, default=0.5)
    ap.add_argument("--models", default="work/models")
    a = ap.parse_args()
    sr = Upscaler(a.models, a.denoise)
    img = cv2.cvtColor(cv2.imread(a.inp), cv2.COLOR_BGR2RGB).astype(np.float32) / 255
    t = time.time()
    out = sr(img)
    print(f"{img.shape[1]}x{img.shape[0]} -> {out.shape[1]}x{out.shape[0]} in {time.time() - t:.2f}s", file=sys.stderr)
    cv2.imwrite(a.out, cv2.cvtColor((out * 255 + 0.5).astype(np.uint8), cv2.COLOR_RGB2BGR))
