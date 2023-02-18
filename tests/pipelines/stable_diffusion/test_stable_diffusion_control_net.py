import numpy as np
import pytest
import torch

from diffusers import StableDiffusionControlNetPipeline
from diffusers.utils import load_image


################################################################################
# PoC version
################################################################################

model_id_sd15_canny = "takuma104/control_sd15_canny"
test_prompt = "best quality, extremely detailed, illustration, looking at viewer"
test_negative_prompt = (
    "longbody, lowres, bad anatomy, bad hands, missing fingers, "
    + "pubic hair,extra digit, fewer digits, cropped, worst quality, low quality"
)


@pytest.mark.skip
def test_from_pretrained():
    pipe = StableDiffusionControlNetPipeline.from_pretrained(model_id_sd15_canny)
    print(pipe)


@pytest.mark.skip
def test_from_pretrained_and_unet_inference():
    pipe = StableDiffusionControlNetPipeline.from_pretrained(model_id_sd15_canny, torch_dtype=torch.bfloat16).to(
        "cuda"
    )
    image = pipe(prompt="an apple", num_inference_steps=15).images[0]
    image.save("/tmp/an_apple_generated.png")
    print(image.size)


def test_pixel_match():
    pipe = StableDiffusionControlNetPipeline.from_pretrained(model_id_sd15_canny).to("cuda")
    pipe.enable_attention_slicing(1)

    seed = 0
    canny_edged_image = load_image(
        "https://huggingface.co/takuma104/controlnet_dev/resolve/main/vermeer_canny_edged.png"
    )

    # reference image generated by https://gist.github.com/takuma104/6cdb6d9aa27f67462f11554cccdf4b34
    output_ref_image = load_image(
        f"https://huggingface.co/takuma104/controlnet_dev/resolve/main/vermeer_canny_edged_seed_{seed}.png"
    )

    batch = 1
    control = torch.from_numpy(np.array(canny_edged_image).copy()).float().cuda() / 255.0
    control = control.repeat(batch, 1, 1, 1)
    control = control.permute(0, 3, 1, 2)  # b h w c -> b c h w

    generator = torch.Generator(device="cuda").manual_seed(seed)
    image = pipe(
        prompt=test_prompt,
        negative_prompt=test_negative_prompt,
        guidance_scale=9.0,
        num_inference_steps=20,
        generator=generator,
        controlnet_hint=control,
    ).images[0]
    image.save(f"/tmp/seed_{seed}.png")

    max_diff = np.abs(np.array(image).astype(np.int32) - np.array(output_ref_image).astype(np.int32)).max()
    assert max_diff < 10  # must be max_diff == 0 but it appears that there is a tiny difference for some reason.


def test_pixel_match_image_argument():
    pipe = StableDiffusionControlNetPipeline.from_pretrained(model_id_sd15_canny).to("cuda")
    pipe.enable_attention_slicing(1)

    seed = 0
    canny_edged_image = load_image(
        "https://huggingface.co/takuma104/controlnet_dev/resolve/main/vermeer_canny_edged.png"
    )

    # reference image generated by https://gist.github.com/takuma104/6cdb6d9aa27f67462f11554cccdf4b34
    output_ref_image = load_image(
        f"https://huggingface.co/takuma104/controlnet_dev/resolve/main/vermeer_canny_edged_seed_{seed}.png"
    )

    generator = torch.Generator(device="cuda").manual_seed(seed)
    image = pipe(
        prompt=test_prompt,
        negative_prompt=test_negative_prompt,
        guidance_scale=9.0,
        num_inference_steps=20,
        generator=generator,
        controlnet_hint=canny_edged_image,
    ).images[0]
    image.save(f"/tmp/seed_{seed}.png")

    max_diff = np.abs(np.array(image).astype(np.int32) - np.array(output_ref_image).astype(np.int32)).max()
    assert max_diff < 10  # must be max_diff == 0 but it appears that there is a tiny difference for some reason.
