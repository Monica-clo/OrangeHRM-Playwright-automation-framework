"""Standalone script - create an employee with a profile photo and record the screen.

What it does (all visible in the browser and in the recorded video):
    1. Start the browser with SCREEN RECORDING turned on
    2. Log in to OrangeHRM
    3. PIM > Add Employee
    4. Enter First / Middle / Last Name and a unique Employee Id
    5. Click the orange '+' on the avatar and add test_data/images/employee_photo.png
    6. Click Save and wait for 'Successfully Saved'
    7. Check the employee page shows the name, Employee Id and the new photo
    8. Stop recording and save the video to reports/videos/

Run (from the project folder, with the virtual environment active):
    python scripts/record_add_employee_with_photo.py
    python scripts/record_add_employee_with_photo.py --first Monica --last N --slowmo 700
    python scripts/record_add_employee_with_photo.py --photo C:/path/to/photo.png --headless
    python scripts/record_add_employee_with_photo.py --browser firefox
"""
from __future__ import annotations

import argparse
import re
import secrets
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from playwright.sync_api import Page, expect, sync_playwright  # noqa: E402

from config.settings import settings  # noqa: E402
from locators.common_locators import CommonLocators, Messages  # noqa: E402
from locators.login_locators import LoginLocators  # noqa: E402
from locators.pim_locators import AddEmployeeLocators, PersonalDetailsLocators  # noqa: E402
from utils.image_utils import validate_profile_photo  # noqa: E402
from utils.screen_recorder import CAPTION_INIT_SCRIPT  # noqa: E402

DEFAULT_PHOTO = PROJECT_ROOT / "test_data" / "images" / "employee_photo.png"


def caption(page: Page, text: str) -> None:
    """Print the step and show it on top of the page, so it is visible in the video."""
    print(f">>> {text}")
    try:
        page.wait_for_load_state("domcontentloaded")
        page.evaluate("text => window.__qaSetCaption && window.__qaSetCaption(text)", text)
    except Exception:  # page was navigating - the caption is optional
        pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an OrangeHRM employee with a profile photo (screen recorded)")
    parser.add_argument("--first", default="Monica", help="First name")
    parser.add_argument("--middle", default="", help="Middle name")
    parser.add_argument("--last", default="N", help="Last name")
    parser.add_argument("--employee-id", default="", help="Employee Id (default: random, max 10 chars)")
    parser.add_argument("--photo", default=str(DEFAULT_PHOTO), help="jpg/png/gif up to 1 MB")
    parser.add_argument("--slowmo", type=int, default=500, help="Delay between actions in ms (for the video)")
    parser.add_argument("--headless", action="store_true", help="Run without showing the browser window")
    parser.add_argument("--browser", default=settings.browser_name, choices=["chromium", "firefox", "webkit"],
                        help="Browser to use (default: BROWSER env var or config)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    photo = Path(args.photo).resolve()
    validate_profile_photo(photo)  # jpg/png/gif and <= 1 MB, otherwise stop with a clear message
    employee_id = (args.employee_id or f"QA{secrets.randbelow(10**8):08d}")[:10]
    full_name = f"{args.first} {args.last}"

    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    video_dir = settings.videos_dir / "_raw" / f"standalone_{stamp}"
    video_file = settings.videos_dir / f"add_employee_with_photo_{employee_id}_{stamp}.webm"
    screenshot_file = settings.screenshots_dir / f"add_employee_with_photo_{employee_id}_{stamp}.png"

    with sync_playwright() as playwright:
        channel = settings.channel_for(args.browser) or None       # e.g. chrome / msedge / moz-firefox
        browser = getattr(playwright, args.browser).launch(headless=args.headless, slow_mo=args.slowmo, channel=channel)
        record = settings.channel_supports_video(channel or "")
        print(f"Browser: {args.browser}{f' (channel {channel})' if channel else ''} - screen recording {'ON' if record else 'OFF (not supported)'}")

        # ------------------------------------------------------------ 1. start screen recording
        video_options = {
            "record_video_dir": str(video_dir),       # <- Playwright records the screen of this context
            "record_video_size": settings.viewport,
        } if record else {}
        context = browser.new_context(viewport=settings.viewport, **video_options)
        context.add_init_script(CAPTION_INIT_SCRIPT)  # step captions on top of every page
        context.set_default_timeout(settings.default_timeout)
        expect.set_options(timeout=settings.expect_timeout)
        page = context.new_page()
        failed = False

        try:
            # -------------------------------------------------------- 2. login
            page.goto(f"{settings.base_url}{settings.login_path}", wait_until="domcontentloaded")
            caption(page, "Step 1: Log in")
            page.locator(LoginLocators.USERNAME_INPUT).fill(settings.username)
            page.locator(LoginLocators.PASSWORD_INPUT).fill(settings.password)
            page.locator(LoginLocators.LOGIN_BUTTON).click()
            expect(page, "Dashboard should open after login").to_have_url(re.compile(r"/dashboard/index"))

            # -------------------------------------------------------- 3. PIM > Add Employee
            caption(page, "Step 2: Open PIM > Add Employee")
            page.locator(CommonLocators.SIDE_MENU_ITEM.format(name="PIM")).click()
            page.locator(CommonLocators.TOP_NAV_TAB.format(name="Add Employee")).click()
            expect(page, "Add Employee page should open").to_have_url(re.compile(r"/pim/addEmployee"))
            employee_id_input = page.locator(AddEmployeeLocators.EMPLOYEE_ID_INPUT)
            expect(employee_id_input, "Employee Id is auto-filled first").to_have_value(re.compile(r"\S+"))

            # -------------------------------------------------------- 4. name + Employee Id
            caption(page, f"Step 3: Enter name '{full_name}' and Employee Id {employee_id}")
            page.locator(AddEmployeeLocators.FIRST_NAME_INPUT).fill(args.first)
            if args.middle:
                page.locator(AddEmployeeLocators.MIDDLE_NAME_INPUT).fill(args.middle)
            page.locator(AddEmployeeLocators.LAST_NAME_INPUT).fill(args.last)
            employee_id_input.fill(employee_id)

            # -------------------------------------------------------- 5. click '+' and add the photo
            caption(page, f"Step 4: Click '+' and add the profile photo '{photo.name}'")
            with page.expect_file_chooser() as chooser:
                page.locator(AddEmployeeLocators.ADD_PROFILE_PICTURE_BUTTON).first.click()
            chooser.value.set_files(str(photo))
            expect(
                page.locator(AddEmployeeLocators.PROFILE_PICTURE_PREVIEW),
                "The avatar should show the added photo",
            ).to_have_attribute("src", re.compile(r"^data:image/"))
            caption(page, "Step 4: Photo added successfully")
            page.wait_for_timeout(1000)  # keep the preview on screen for the recording

            # -------------------------------------------------------- 6. save
            caption(page, "Step 5: Click Save")
            page.locator(AddEmployeeLocators.SAVE_BUTTON).click()
            expect(
                page.locator(CommonLocators.TOAST_MESSAGE).first,
                "'Successfully Saved' message should appear",
            ).to_contain_text(Messages.SUCCESSFULLY_SAVED)
            expect(page, "Employee details page should open").to_have_url(
                re.compile(r"/pim/viewPersonalDetails/empNumber/\d+")
            )

            # -------------------------------------------------------- 7. verify saved employee + photo
            caption(page, "Step 6: Verify the saved employee and the profile photo")
            expect(page.locator(PersonalDetailsLocators.EMPLOYEE_NAME_HEADER)).to_have_text(full_name)
            expect(page.locator(PersonalDetailsLocators.FIRST_NAME_INPUT)).to_have_value(args.first)
            expect(page.locator(PersonalDetailsLocators.EMPLOYEE_ID_INPUT)).to_have_value(employee_id)
            avatar = page.locator(PersonalDetailsLocators.PROFILE_PICTURE)
            expect(avatar, "Saved photo should replace the default avatar").to_have_attribute(
                "src", re.compile(r"^(?!.*default-photo).+")
            )
            caption(page, f"Done: employee {employee_id} saved with profile photo")
            screenshot_file.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(screenshot_file))
            page.wait_for_timeout(1500)
            print(f"\nPASSED - employee '{full_name}' ({employee_id}) created with photo '{photo.name}'")
            print(f"Employee page: {page.url}")
        except Exception as error:
            failed = True
            print(f"\nFAILED - {error}")
            screenshot_file.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(screenshot_file), full_page=True)
        finally:
            # -------------------------------------------------------- 8. stop recording + save video
            video = page.video
            context.close()                            # the video file is completed on close
            if video:
                video_file.parent.mkdir(parents=True, exist_ok=True)
                video.save_as(str(video_file))
                video.delete()
                print(f"Screen recording: {video_file}")
            browser.close()
            print(f"Screenshot:       {screenshot_file}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
