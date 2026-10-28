# Higgsfield pipeline for wheel renders

## Tools

Load the Higgsfield tools with ToolSearch, for example `select:mcp__Higgsfield__generate_image_batch,mcp__Higgsfield__jobs_wait,mcp__Higgsfield__show_generation_by_ids,mcp__Higgsfield__media_upload_widget`.

- **Model:** `gpt_image_2_5` (OpenAI GPT Image 2.5).
  - It takes up to several `image_references`.
  - A reference `value` can be a media ID or the job ID of an earlier generation.
  - Aspect ratios: 16:9, 4:5, 1:1 and more.
- **Quality:** `xhigh` at `2k` for anything shown to the client.
  - `high` at `2k` costs about 2.75 credits per image.
  - `xhigh` costs more, but still only a few credits.
  - Check the cost with `generate_image` and `get_cost: true`. The batch tool can't check cost.
- **Before the first generation,** call `get_preferences`. If `auto_create_project` is false, leave out `folder_id`.
- **Independent shots:** send them in one `generate_image_batch`.
  - Then call `jobs_wait`, which waits at most 15 s per call, so call it again until every job is finished.
  - Then make **one** `show_generation_by_ids` call.
- **Variants of the same edit:** use `generate_image` with `count: 2`.

## Getting the sketch and logo in

1. Try the direct path first: `media_upload` → `curl PUT` to the `upload_url` → `media_confirm`.
2. In this cloud sandbox the egress policy refuses `upload.higgsfield.ai` (403 on CONNECT). Do not retry it or route around it.
   - Call `media_upload_widget` as the only tool in that turn.
   - The user uploads the files in the browser and replies with the media IDs.
3. The result CDN (`d8j0ntlcm91z4.cloudfront.net`) is not reachable from the sandbox either. You can link the images, but you can't view or composite them here. Tell the user so.
   - If the client needs a pixel-exact logo composite done here, ask them to allow both hosts in the environment's network settings. Read the `environment.network` documentation page.

## Revision loop

1. Read the client's note. If they attach a render, look at it carefully: it is your only view of the output.
2. Choose the base image, either the job ID they approved or the one they attached. To identify an attachment, compare it with earlier results by shot type and scene.
3. Build the edit from three references, in this order:
   1. the image being edited;
   2. the logo file;
   3. an approved render with a correct logo.
   
   Then write the "keep everything identical, change only …" prompt.
4. Generate 1–2 variants, show them, link them, and ask the client to check the logo.
5. Each design decision the client confirms (finish, construction, cap style) goes into `SKILL.md` → Client preferences.
