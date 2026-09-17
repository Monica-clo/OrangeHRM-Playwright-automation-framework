# OrangeHRM – Hybrid UI + API Automation Framework

This framework automates the **Employee Lifecycle Management** scenario on https://opensource-demo.orangehrmlive.com/. It combines **UI tests** (Playwright) and **API tests** in one Python/Pytest project. The API tests use exactly **5 ReqRes APIs**: `POST /api/users`, `PUT /api/users/2`, `PATCH /api/users/2`, `DELETE /api/users/2` and `GET /api/users?delay=2`. The project follows the **Page Object Model**, reads its test data from JSON/CSV, validates API responses against JSON schemas, produces HTML and Allure reports, records a video of every UI test, and runs in **CI/CD** on GitHub Actions or Jenkins.

---

## 1. Coverage of the assessment

| # | Step | How it is automated | File |
|---|---|---|---|
| 1 | **Login** as `Admin` / `admin123` | UI login, verified by the Dashboard URL, header and user menu. | `tests/hybrid/test_employee_lifecycle_e2e.py` |
| 2 | **Add employee** from PIM › Add Employee | Data comes from `employees.json` or `.csv`. The test enters First, Middle and Last Name and a unique Employee Id. It then clicks the orange **+** on the avatar, selects `employee_photo.png` in the file chooser, and checks the preview. It optionally creates login details, then clicks **Save**. It then checks the "Successfully Saved" toast, the Personal Details page, the avatar, and the Employee List search. | same |
| 3 | **Edit employee** | The test searches by Employee Id and opens the record. It then **changes the profile photo**: it clicks the avatar, uploads `test_data/images/profile_picture.png` on the Change Profile Picture page, saves, and checks the toast. Back on Personal Details, it checks that the avatar really changed by comparing screenshots and image size before and after. Next it updates Job Title and Employment Status. It checks the toast, reloads the page to confirm the values were saved, and checks the Employee List columns. | same |
| 4 | **Validate via API** (simulated with ReqRes) | The employee is read from the UI and compared with the test data. Then:<br>• `POST /api/users` with the UI name and job title → **201**, and the response must return the same values.<br>• `PUT /api/users/{id}` → **200**, with the same values echoed.<br>• `PATCH /api/users/{id}` with the Employment Status → **200**, with the same value echoed. | same |
| 5 | **Delete employee** | The employee is deleted in the UI and the "Successfully Deleted" toast is checked. A new UI search must show "No Records Found". Then `DELETE /api/users/{id}` must return **204** with an empty body. | same |
| 6 | **Logout** | The test logs out through the user menu, checks the login page is shown, and confirms the session is invalid: opening the dashboard URL redirects to login. | same |
| + | **ReqRes API suite** | `POST /api/users` (201), `PUT /api/users/2` (200), `PATCH /api/users/2` (200), `DELETE /api/users/2` (204) and `GET /api/users?delay=2` (200). Each test checks the status code, the response schema, the echoed fields, the timestamps, the empty body on delete, and the response delay. | `tests/api/test_reqres_user_apis.py` |
| + | **Add employee with photo (recorded)** | A focused, screen-recorded UI test: open Add Employee, enter the name and Employee Id, click **+** and add `employee_photo.png`, check the preview, click **Save**, check the toast and saved photo, and find the employee in the Employee List. | `tests/ui/test_add_employee_with_photo.py` |
| + | **UI extras** | Login with an invalid password; logout; Personal Details and Contact Details updates. | `tests/ui/` |

---

## 2. Why "hybrid"

| Layer | Implementation |
|---|---|
| **UI – Page Object Model** | `pages/`: one class per screen, with business-level methods. |
| **UI – locator repository** | `locators/`: named constants that match the labels shown in the app. |
| **API – service clients** | `api/base_client.py` wraps Playwright's `APIRequestContext` and adds logging, Allure attachments, throttling, retries on 429, and status assertions. `reqres_client.py` provides the 5 endpoint methods. |
| **API – contract tests** | `api/schemas.py` holds JSON schemas, validated with `jsonschema`. A failure lists every violation in one message. |
| **UI → API bridge** | `api/models.py` defines `EmployeeSnapshot`, built from the Employee List row. It is compared with the test data and used as the request body for the API calls. |
| **Data-driven** | `test_data/employees.json` or `.csv` (UI and hybrid tests) and `test_data/api/reqres_test_data.json` (API tests). |
| **Config-driven** | `config/config.yaml`, where every value can be overridden by an environment variable. |

---

## 3. Framework structure

```
orangehrm-playwright-automation/
├── .github/workflows/hybrid-tests.yml   # CI: API job, UI+hybrid job, combined Allure report
├── Jenkinsfile                          # Jenkins alternative
├── api/
│   ├── base_client.py                   # APIRequestContext wrapper (log, retry, throttle, assert)
│   ├── reqres_client.py                 # the 5 ReqRes APIs (POST, PUT, PATCH, DELETE, delayed GET)
│   ├── models.py                        # EmployeeSnapshot (employee data read from the UI)
│   └── schemas.py                       # JSON schemas for the 5 APIs + assert_schema()
├── config/
│   ├── config.yaml                      # URLs, credentials, timeouts, ReqRes settings
│   └── settings.py                      # YAML + environment overrides
├── locators/                            # common / login / PIM locators
├── pages/                               # Page Objects (login, dashboard, PIM pages, profile tabs)
├── tests/
│   ├── api/                             # @api     ReqRes POST / PUT / PATCH / DELETE / delayed GET
│   ├── ui/                              # @ui      add employee with photo (recorded), login/logout,
│   │                                    #          personal & contact details
│   └── hybrid/                          # @hybrid  full 6-step lifecycle (UI + API)
├── test_data/
│   ├── employees.json / employees.csv   # employee data (UI + hybrid)
│   ├── employee_profile.json            # personal / contact details
│   ├── api/reqres_test_data.json        # API inputs + expected values
│   └── images/employee_photo.png        # photo added with the '+' button when creating the employee
│       images/profile_picture.png       # different photo uploaded while editing the employee
├── scripts/record_add_employee_with_photo.py  # standalone: add employee + photo + Save, screen recorded
├── tools/collect_evidence.py            # copies report + videos into evidence/ for the repo
├── utils/                               # data models, data reader, logger, steps, image helper,
│                                        # screen_recorder.py (video naming + on-screen step captions)
├── conftest.py                          # fixtures (browser context, video, trace, ReqRes, cleanup) + report hooks
├── pytest.ini                           # markers, HTML
├── requirements.txt
└── run_tests.bat / run_tests.sh
```

Each test is marked automatically from its folder: `api`, `ui` or `hybrid`.

---

## 4. Setup

**Prerequisites:** Python 3.10 or newer (3.12 recommended) and Git.

### Windows
```bat
cd orangehrm-playwright-automation
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
```
- **PowerShell:** activate with `.venv\Scripts\Activate.ps1`. If scripts are blocked, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.
- **App Control / Smart App Control:** if Windows blocks `pytest.exe`, always use `python -m pytest ...`, which every command below already does.

### macOS / Linux
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install --with-deps chromium
```

---

## 5. How to run

| Goal | Command |
|---|---|
| Everything (API + UI + hybrid) | `python -m pytest` |
| **Assessment scenario** (steps 1–6) | `python -m pytest -m hybrid --headed` |
| API tests only (no browser needed) | `python -m pytest -m api` |
| UI tests only | `python -m pytest -m ui` |
| Smoke tests | `python -m pytest -m smoke` |
| **Standalone recorded script** (no pytest): create an employee, add the photo with **+**, save | `python scripts/record_add_employee_with_photo.py` |
| **Recorded "add employee with photo" test** | `python -m pytest tests/ui/test_add_employee_with_photo.py --headed` |
| Slow motion, for an easy-to-watch recording | `set SLOW_MO_MS=500` (or add `--slowmo 500`), then run |
| Use Microsoft Edge (if Chromium is blocked) | `python -m pytest -m hybrid --browser-channel msedge` |
| Use CSV employee data | `set DATA_SOURCE=csv` (Windows) or `export DATA_SOURCE=csv`, then run |
| Retry flaky tests | `python -m pytest --reruns 1` (a used-up ReqRes daily quota is never rerun: `--rerun-except=ApiQuotaExceededError` is set in `pytest.ini`) |
| Name the HTML report | `python -m pytest -m api --html=reports/html/api-report.html` |
| Helper script | `run_tests.bat hybrid --headed` or `./run_tests.sh api` |

### Hybrid (UI + API) in Chrome AND Firefox
Pass `--browser` once per browser. Every UI and hybrid test then runs once in each browser; API tests run only once.
```powershell
$env:CHROMIUM_CHANNEL="chrome"        # installed Google Chrome ("msedge" = Microsoft Edge, empty = Playwright Chromium)
$env:FIREFOX_CHANNEL="moz-firefox"    # installed Mozilla Firefox (empty = Playwright Firefox)
python -m pytest -m "hybrid or api" --browser chromium --browser firefox -n 2 --html=reports/html/chrome-firefox-report.html --self-contained-html
```
- `CHROMIUM_CHANNEL` and `FIREFOX_CHANNEL` pick the installed browser **per engine**, so a single run can use Google Chrome and Mozilla Firefox together. `--browser-channel` on the command line applies to *all* browsers and overrides both.
- `$env:BROWSER="chromium,firefox"` makes both browsers the default, so the `--browser` options can be omitted.
- In `moz-firefox` mode Playwright cannot record video, so recording is switched off automatically for Firefox only. Chrome runs are still recorded. With Playwright's own Firefox (for example in CI), recording works.
- Test names, videos and report rows include the browser, e.g. `[chromium-…]` and `[firefox-…]`.
- In CI, the workflow runs one job per browser (a matrix of Chromium and Firefox) and merges both into one Allure report.

### Parallel execution in Firefox
The framework uses **pytest-xdist** for parallel runs. Every test gets its own browser context, video and unique test data, so tests don't interfere with each other.
```bat
python -m playwright install firefox
python -m pytest --browser firefox -n 4
python -m pytest --browser firefox -n auto
python -m pytest -m "ui or hybrid" --browser firefox -n 2 --headed
```
- `-n 4` runs 4 tests at the same time; `-n auto` uses one worker per CPU core.
- To make Firefox the default, `set BROWSER=firefox` (or set `browser.name` in `config.yaml`). `--browser` on the command line always wins.
- The 5 ReqRes API tests are kept on one worker (`xdist_group`, with `--dist=loadgroup` in `pytest.ini`), so the ReqRes rate limit is respected.
- Old Allure results are cleaned once at the start, never by the workers. Each worker writes its own log file, `reports/logs/test_run_gw0.log` and so on.
- The shared demo site can be slow, so 2–4 workers is a sensible range.

### Key environment variables
| Variable | Default | Purpose |
|---|---|---|
| `ORANGEHRM_USERNAME` / `ORANGEHRM_PASSWORD` | `Admin` / `admin123` | Login |
| `BROWSER` | `chromium` | Default browser(s): `chromium`, `firefox`, `webkit` or a list such as `chromium,firefox` |
| `CHROMIUM_CHANNEL` | empty | `chrome` = Google Chrome, `msedge` = Microsoft Edge, empty = Playwright Chromium |
| `FIREFOX_CHANNEL` | empty | `moz-firefox` = installed Mozilla Firefox (experimental, no video), empty = Playwright Firefox |
| `DATA_SOURCE` | `json` | `json` or `csv` |
| `REQRES_BASE_URL` | `https://reqres.in` | Public test API |
| `REQRES_API_KEY` | empty | Sent as `x-api-key` only when set |
| `REQRES_SKIP_ON_QUOTA` | `false` | When the ReqRes **daily** quota is used up, report the API steps as *skipped* instead of *failed* |
| `REQRES_USERS_MIN_INTERVAL` | `3.2` s | Throttle, because ReqRes allows 20 requests/minute on `/api/users` |
| `CLEANUP_CREATED_EMPLOYEES` | `true` | Deletes employees left behind by failed runs |
| `RECORD_VIDEO` | `true` | UI screen recording of every UI and hybrid test |
| `VIDEO_CAPTIONS` | `true` | Shows the current step as a caption on the recorded screen |
| `SLOW_MO_MS` | `0` | Slows every browser action down, for example to `500`, so the recording is easy to follow |
| `TRACING` | `retain-on-failure` | Playwright trace for debugging |
| `EXPECT_TIMEOUT` / `DEFAULT_TIMEOUT` | `20000` ms | Increase if the demo site is slow |

---

## 6. Reports and evidence

| Artifact | Location |
|---|---|
| HTML report, with the video and failure screenshot embedded and the API request/response logs | `reports/html/report.html` |
| **UI screen recordings** (one per test, with step captions) | `reports/videos/<test name>.webm`, e.g. `test_add_employee_with_profile_photo_chromium-fulltime_qa_engineer_with_login.webm`. The recordings are also embedded in the HTML report and attached to Allure. |
| Failure screenshots, plus avatar screenshots taken before and after the photo change | `reports/screenshots/` |
| Playwright traces (on failure) | `reports/traces/*.zip`. Open with `python -m playwright show-trace <zip>`. |
| Execution log | `reports/logs/test_run.log` |

To open the HTML report on Windows, run `start reports\html\report.html`.

**How the screen recording works:** `conftest.py` records every browser context. When the test ends, the video is saved under the test's name. The `screen_recorder` fixture (`utils/screen_recorder.py`) shows each `with screen_recorder.step("...")` title as a caption at the top of the page, so the video explains itself. Videos play in Chrome and Edge; to convert one to MP4, you can use any video converter or `ffmpeg -i in.webm out.mp4`.

**Adding the evidence to GitHub:** the assessment asks for the HTML report and the video in the repository, but `reports/` is overwritten on every run. After a good run, execute:
```bat
python tools/collect_evidence.py
git add evidence
git commit -m "Add test execution evidence"
```
This copies the report, videos and screenshots into `evidence/run_<date>/`. If the video is large, you can upload it to Google Drive instead and put the link in this README.

---

## 7. CI/CD

### GitHub Actions: `.github/workflows/hybrid-tests.yml`
| Job | What it does |
|---|---|
| `api-tests` | Installs the requirements and runs `pytest -m api` (no browser needed). Publishes the JUnit results and uploads the reports. |
| `ui-hybrid-tests` | Installs the selected browser (**Firefox** by default) and runs `pytest -m "ui or hybrid" -n <workers>` in parallel, with video. Publishes the results and uploads the reports, videos and traces. |
| `allure-report` | Merges the Allure results from both jobs into one Allure report and uploads it. On `main` it also publishes the report to GitHub Pages under `/allure`. |

- **Triggers:** push to `main`/`develop`, pull requests to `main`, a nightly schedule, and a manual run where you choose the suite, browser and data source.
- **Secrets** (optional, under Settings › Secrets and variables › Actions): `ORANGEHRM_USERNAME`, `ORANGEHRM_PASSWORD`, `REQRES_API_KEY`.
- **GitHub Pages:** enable it once under Settings › Pages, using the `gh-pages` branch.

**Pushing the project:**
```bash
git init
git add .
git commit -m "Hybrid UI + API automation framework for OrangeHRM"
git branch -M main
git remote add origin https://github.com/<you>/orangehrm-playwright-automation.git
git push -u origin main
```

### Jenkins: `Jenkinsfile`
- Runs inside the official `mcr.microsoft.com/playwright/python` image, with separate **API** and **UI + Hybrid** stages. A failure in one stage marks the build unstable without skipping the other stage.
- Publishes the JUnit results and HTML reports, and archives `reports/**`.
- **Jenkins setup:** add the credential `orangehrm-credentials` (username/password).

---

## 8. APIs used by the tests (the only 5 APIs in the framework)

**ReqRes** (`https://reqres.in`, public demo endpoints). The API suite checks these calls:
| Method | Endpoint | Body | Expected |
|---|---|---|---|
| POST | `/api/users` | `{"name":"morpheus","job":"leader"}` | 201, echoes `name`/`job` plus `id` and `createdAt` |
| PUT | `/api/users/2` | `{"name":"morpheus","job":"zion resident"}` | 200, echoes the body plus `updatedAt` |
| PATCH | `/api/users/2` | `{"job":"zion resident"}` | 200, echoes `job` plus `updatedAt` |
| DELETE | `/api/users/2` | none | 204, empty body |
| GET | `/api/users?delay=2` | none | 200 after at least 2 seconds; page 1 with 6 users (ids 1–6), total 12 |

ReqRes rate-limits `/api/users` to 20 requests per minute per IP. The client spaces those calls about 3.2 seconds apart and retries on HTTP 429, honouring `Retry-After`.

---

## 9. Test data

- **`employees.json` / `.csv`:** one record per lifecycle run. `profile_picture` is the photo uploaded when the employee is added, and `edit_profile_picture` is the new photo uploaded during the edit step (jpg, png or gif, up to 1 MB; leave it empty to skip that step). The Employee Id and username get a random suffix at run time, because the demo site is shared.
- **`api/reqres_test_data.json`** (the `user_apis` section): the request bodies, user ids, expected status codes and delay settings for the 5 API tests. To test other values, change the JSON; the script stays the same.
- **Dropdown values:** `job_title` and `employment_status` must exist in the demo. If one is missing, the error message lists the available options.

---

## 10. UI locator map (from the application screenshots)

Most form fields are located by their **visible label**, using the `INPUT_BY_LABEL` and `SELECT_BY_LABEL` templates in `common_locators.py`. As a result, locator names read like the UI.

**Add Employee** (screenshots 1–2): `AddEmployeeLocators`
| UI element | Locator name | Selector |
|---|---|---|
| First Name | `FIRST_NAME_INPUT` | `input[name='firstName']` |
| Middle Name | `MIDDLE_NAME_INPUT` | `input[name='middleName']` |
| Last Name | `LAST_NAME_INPUT` | `input[name='lastName']` |
| Employee Id | `EMPLOYEE_ID_INPUT` | input under the label "Employee Id" |
| Orange **+** on the avatar (opens the file chooser) | `ADD_PROFILE_PICTURE_BUTTON` | `button.employee-image-action` |
| Hidden photo file input (fallback) | `PROFILE_PICTURE_FILE_INPUT` | `input[type='file']` |
| "Accepts jpg, .png, .gif up to 1MB" hint | `PROFILE_PICTURE_HINT` | text locator |
| Avatar preview | `PROFILE_PICTURE_PREVIEW` | `img.employee-image` |
| Create Login Details toggle | `CREATE_LOGIN_DETAILS_TOGGLE` | `div.oxd-switch-wrapper span.oxd-switch-input` |
| Username | `USERNAME_INPUT` | input under the label "Username" |
| Status Enabled / Disabled | `STATUS_ENABLED_RADIO` / `STATUS_DISABLED_RADIO` | the label "Enabled" / "Disabled" |
| Password / Confirm Password | `PASSWORD_INPUT` / `CONFIRM_PASSWORD_INPUT` | input under the matching label |
| Cancel / Save | `CANCEL_BUTTON` / `SAVE_BUTTON` | `button:has-text('Cancel')` / `button[type='submit']` |

**Personal Details** (screenshots 3–4): `PersonalDetailsLocators`
| UI element | Locator name |
|---|---|
| Name above avatar ("Monica N") | `EMPLOYEE_NAME_HEADER` |
| Employee Id / Other Id | `EMPLOYEE_ID_INPUT` / `OTHER_ID_INPUT` |
| Driver's License Number / License Expiry Date | `DRIVERS_LICENSE_NUMBER_INPUT` / `LICENSE_EXPIRY_DATE_INPUT` |
| Nationality / Marital Status | `NATIONALITY_DROPDOWN` / `MARITAL_STATUS_DROPDOWN` |
| Date of Birth | `DATE_OF_BIRTH_INPUT` |
| Gender Male / Female | `GENDER_MALE_RADIO` / `GENDER_FEMALE_RADIO` |
| Save (Personal Details) | `PERSONAL_DETAILS_SAVE_BUTTON` |
| Blood Type / Test_Field / Save (Custom Fields) | `BLOOD_TYPE_DROPDOWN` / `TEST_FIELD_INPUT` / `CUSTOM_FIELDS_SAVE_BUTTON` |
| Left tabs (Personal Details, Contact Details, Job …) | `TAB_*` constants |

**Change Profile Picture** (opened by clicking the avatar): `ChangeProfilePictureLocators`
| UI element | Locator name |
|---|---|
| Avatar in the left panel (click to open the page) | `AVATAR_LINK` / `PROFILE_PICTURE` |
| "Change Profile Picture" title | `PAGE_TITLE` |
| Photo file input / preview | `PHOTO_FILE_INPUT` / `PHOTO_PREVIEW` |
| Save | `SAVE_BUTTON` |

**Contact Details** (screenshot 5): `ContactDetailsLocators`
| UI element | Locator name |
|---|---|
| Street 1 / Street 2 / City | `STREET_1_INPUT` / `STREET_2_INPUT` / `CITY_INPUT` |
| State/Province / Zip/Postal Code / Country | `STATE_PROVINCE_INPUT` / `ZIP_POSTAL_CODE_INPUT` / `COUNTRY_DROPDOWN` |
| Telephone: Home / Mobile / Work | `HOME_TELEPHONE_INPUT` / `MOBILE_INPUT` / `WORK_TELEPHONE_INPUT` |
| Work Email / Other Email | `WORK_EMAIL_INPUT` / `OTHER_EMAIL_INPUT` |

**Job tab and Employee List** (step 3)
| UI element | Locator name |
|---|---|
| Job Title / Employment Status dropdowns | `JobDetailsLocators.JOB_TITLE_DROPDOWN` / `EMPLOYMENT_STATUS_DROPDOWN` |
| Employee Id search box / Search button | `EmployeeListLocators.EMPLOYEE_ID_INPUT` / `SEARCH_BUTTON` |
| Result rows / cells / edit icon | `TABLE_ROWS` / `ROW_CELLS` / `ROW_EDIT_ICON` |

**Common** (every page): `CommonLocators`. This covers the top bar header (`MODULE_HEADER`), the user menu (`USER_DROPDOWN`), the side menu (`SIDE_MENU_ITEM`), the PIM tabs (`TOP_NAV_TAB`), toasts (`TOAST_MESSAGE`) and dropdown options (`DROPDOWN_OPTION`).

---

## 11. Dependencies

| Package | Purpose |
|---|---|
| `playwright` | Browser automation, API requests (`APIRequestContext`), video and tracing |
| `pytest` | Test runner |
| `pytest-playwright` | Browser fixtures and CLI options (`--browser`, `--headed`, `--slowmo`, `--browser-channel`) |
| `pytest-html` | Self-contained HTML report |
| `allure-pytest` | Allure results with steps and API attachments |
| `pytest-rerunfailures` | Retries for runs against the shared demo sites |
| `pytest-xdist` | Parallel execution (`-n 4`) |
| `jsonschema` | Validating API responses against contracts |
| `PyYAML` | Reading the configuration file |

---

## 12. Troubleshooting

| Symptom | Fix |
|---|---|
| `pytest.exe ... blocked by Application Control policy` | Use `python -m pytest`. |
| `Could not open requirements file` | You are in the wrong folder. `cd` into the folder that contains `requirements.txt`. |
| ReqRes returns **401** or **403** | ReqRes may require a key. Create a free one at app.reqres.in and set `REQRES_API_KEY`. |
| ReqRes returns **429** "demo limit of 40 requests/day" | The anonymous daily quota is used up (it resets at midnight UTC), so the client stops immediately instead of retrying. Create a free account at app.reqres.in, copy your API key, and set `REQRES_API_KEY` for a higher limit. Alternatively, set `REQRES_SKIP_ON_QUOTA=true` to report those steps as skipped. |
| ReqRes returns **429** for a short burst | The client retries automatically, honouring `Retry-After`. |
| "Personal Details title should be visible" under parallel load | The demo site is slow. The page object reloads once automatically. If it still fails, use fewer workers (`-n 2`), raise `EXPECT_TIMEOUT=40000`, or add `--reruns 1`. |
| ReqRes is blocked on your network | The API and hybrid tests need access to reqres.in. Try another network, or run only the UI tests with `-m ui`. |
| `Option 'QA Engineer' is not available` | The shared demo data changed. Use one of the options listed in the error. |
| Timeouts | Increase `EXPECT_TIMEOUT`, or run with `--reruns 1`. |
| Debugging a UI failure | Run `python -m playwright show-trace reports/traces/<test>.zip`. |
