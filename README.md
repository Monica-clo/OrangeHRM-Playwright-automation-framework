
---

## 4. Tagging strategy

Every test lives under `tests/e2e/` and carries these tags (pytest markers, enforced by `--strict-markers`, so a typo'd tag fails collection instead of silently not running):

| Tag | Meaning | Workflows |
|---|---|---|
| `e2e` | added automatically to everything under `tests/e2e` | 1–5 |
| `workflow` | one of the 5 workflows | 1–5 |
| `positive` | happy path | 2, 3, 4, 5 |
| `negative` | the request must be rejected | 1 |
| `smoke` | fast critical checks | 1, 2 |
| `regression` | extended coverage | 3, 4, 5 |

Tags are **orthogonal, not a hierarchy** — a test can be `workflow` + `positive` + `smoke` at once. This is what lets CI run a fast `smoke` gate on every push and save `regression` for nightly, without maintaining separate test files.

---

## 5. How to run — UI, API and Performance commands

Every workflow test (`tests/e2e/test_employee_workflows.py`) already combines **UI + API in a single test** — e.g. workflow 2 does the PIM UI steps, then calls `POST /api/users` and validates it inline. There is no separate "UI-only" or "API-only" pytest suite to merge; running the workflow tests runs both together. The one genuinely separate suite is the **k6 performance test**.

### UI + API (pytest / Playwright)

| Goal | Command |
|---|---|
| All 5 workflows (UI + API) | `python -m pytest -m workflow` |
| The negative workflow only | `python -m pytest -m negative` |
| The 4 positive workflows | `python -m pytest -m positive --headed` |
| Smoke / regression | `python -m pytest -m smoke` / `python -m pytest -m regression` |
| One specific workflow | `python -m pytest -k workflow_3 --headed` |
| In parallel (2 workers) | `python -m pytest -m workflow -n 2` |
| Chrome **and** Firefox | `python -m pytest -m workflow --browser chromium --browser firefox -n 2` |
| Slow motion, easy-to-watch video | PowerShell: `$env:SLOW_MO_MS=500 ; python -m pytest -m workflow` |
| Another environment | PowerShell: `$env:ORANGEHRM_BASE_URL="https://staging.example.com" ; $env:ORANGEHRM_USERNAME="..." ; python -m pytest -m workflow` |
| CSV instead of JSON employee data | PowerShell: `$env:DATA_SOURCE="csv" ; python -m pytest -m workflow` |
| Via helper script | `.\run_tests.bat workflow` (Windows) / `./run_tests.sh workflow` (macOS/Linux) |

### Performance (k6)

```powershell
mkdir reports\performance -ErrorAction SilentlyContinue
k6 run performance/k6/api-performance.js
```
Load profile (needs a ReqRes API key):
```powershell
k6 run -e PERF_PROFILE=load -e REQRES_API_KEY=your_key_here performance/k6/api-performance.js
```
Via helper script:
```powershell
.\run_tests.bat perf
```
Without installing k6 (Docker):
```powershell
docker run --rm -i -v "${PWD}:/work" -w /work grafana/k6 run performance/k6/api-performance.js
```
If `k6` isn't on PATH yet, call it directly:
```powershell
& "C:\Program Files\k6\k6.exe" run performance/k6/api-performance.js
```

### Run UI+API and Performance back-to-back, one command

PowerShell (use `;`, not `&&`):
```powershell
python -m pytest -m workflow ; .\run_tests.bat perf
```
macOS/Linux:
```bash
python -m pytest -m workflow && ./run_tests.sh perf
```

**Environment-based execution:** nothing is hard-coded. `config/config.yaml` holds the defaults and every value is overridden by an environment variable (URL, credentials, browser, data source, timeouts, ReqRes URL and key). CI passes them as environment variables and secrets — the same code runs locally, in GitHub Actions and in Jenkins without any code change.

### Environment variables
| Variable | Default | Purpose |
|---|---|---|
| `ORANGEHRM_BASE_URL` | demo site | Environment under test |
| `ORANGEHRM_USERNAME` / `ORANGEHRM_PASSWORD` | `Admin` / `admin123` | Login |
| `BROWSER` | `chromium` | `chromium`, `firefox`, `webkit` or a list such as `chromium,firefox` |
| `CHROMIUM_CHANNEL` / `FIREFOX_CHANNEL` | empty | `chrome`/`msedge` = installed browser; `moz-firefox` = installed Firefox (no video) |
| `DATA_SOURCE` | `json` | `json` or `csv` |
| `REQRES_BASE_URL` / `REQRES_API_KEY` | `https://reqres.in` / empty | ReqRes host and `x-api-key` |
| `REQRES_SKIP_ON_QUOTA` | `false` | Report the API step as *skipped* (not failed) when the ReqRes **daily** quota is used up |
| `REQRES_USERS_MIN_INTERVAL` | `3.2` s | Throttle for `/api/users` (20 requests/minute limit) |
| `API_MAX_RESPONSE_MS` | `5000` | Maximum response time accepted by `validate_response()` |
| `CLEANUP_CREATED_EMPLOYEES` | `true` | Delete employees left behind by failed runs |
| `RECORD_VIDEO` / `VIDEO_CAPTIONS` / `SLOW_MO_MS` / `TRACING` | `true` / `true` / `0` / `retain-on-failure` | Recording and tracing |
| `EXPECT_TIMEOUT` / `DEFAULT_TIMEOUT` / `NAVIGATION_TIMEOUT` | `20000` / `20000` / `45000` ms | Increase if the demo site is slow |
| `PERF_PROFILE` and `THRESHOLD_*` | `smoke` | k6 settings, see section 2 |

---

## 6. Reports and evidence

| Artifact | Location |
|---|---|
| HTML report (video and failure screenshot embedded, API logs) | `reports/html/report.html` |
| Allure results (UI steps plus API request/response attachments) | `reports/allure-results` – view with `allure serve reports/allure-results` |
| **Videos** (one per workflow, with on-screen step captions) | `reports/videos/<test name>.webm` |
| **Screenshots** on failure, plus avatar before/after | `reports/screenshots/` |
| Playwright traces (on failure) | `reports/traces/*.zip` – open with `python -m playwright show-trace <zip>` |
| Execution log / JUnit XML | `reports/logs/`, `reports/junit/results.xml` |
| **k6 report** | `reports/performance/k6-report.html`, `k6-summary.json` |

`reports/` is overwritten on every run. To commit the evidence the assessment asks for, run `python tools/collect_evidence.py`, then `git add evidence` (it copies the report, videos, screenshots and k6 report into `evidence/run_<date>/`).

---

## 7. CI/CD – `.github/workflows/ci.yml`

| Job | What it does |
|---|---|
| `e2e-tests` | Matrix: **one job per browser** (Chromium, Firefox), each running `pytest -m <tag> -n <workers>` with **xdist parallel workers** and automatic reruns. Installs dependencies and the browser, publishes the JUnit results, and uploads the HTML report, videos, screenshots, traces and Allure results as an artifact. |
| `performance-tests` | Installs k6 and runs `k6 run performance/k6/api-performance.js`. The thresholds decide pass/fail; `k6-report.html` and `k6-summary.json` are uploaded as an artifact. Runs on the nightly schedule or manually, **not** on every push, because the free ReqRes tier has a small daily quota. |
| `allure-report` | Merges the Allure results of all browser jobs into one report and uploads it (published to GitHub Pages on `main`). |

- **Triggers:** push to `main`/`develop`, pull requests to `main`, a nightly schedule, and a manual run where you choose the suite (`all`, `e2e`, `performance`), the tag, browsers, workers, data source, environment URL and k6 profile.
- **Secrets** (optional): `ORANGEHRM_USERNAME`, `ORANGEHRM_PASSWORD`, `REQRES_API_KEY`.
- **Jenkins:** `Jenkinsfile` has the same two stages (Playwright image, then the `grafana/k6` image) and publishes the same reports.

---

## 8. Test stability and flaky-test strategy

**Implemented in the framework**
| Technique | How |
|---|---|
| Test-level retry | `pytest.ini`: `--reruns=2 --reruns-delay=3` (pytest-rerunfailures). A test that fails anywhere in its run gets re-executed from scratch after a pause; a used-up ReqRes *daily* quota is never retried (`--rerun-except=ApiQuotaExceededError`). |
| Navigation-level retry | `pages/base_page.py::navigate()` retries once on a `page.goto()` timeout — covers pure first-request site slowness before any app code has run, without rerunning the whole test. |
| Smart waiting | No fixed sleeps in tests. Playwright auto-waiting plus `expect()` assertions poll up to `EXPECT_TIMEOUT`; page objects wait for the table, toast or page-ready state; `DashboardPage.verify_loaded()` waits for network-idle and the dashboard widgets to actually render (not just the URL/header) before the next click, to avoid racing the SPA's post-login hydration. |
| Screenshots on failure | `conftest.py` saves a full-page screenshot, embeds it in the HTML report and attaches it to Allure. Video and a Playwright trace are kept as well. |
| Isolation | Unique Employee Ids and emails per run, one browser context per test, no test depends on another, and leftover employees are deleted after a failed run. |
| Clear login failures | If the demo answers `Invalid credentials` for the configured user, the test stops at once and says so instead of timing out on the Dashboard. |

**Detection:** a test that fails and then passes on a rerun is shown as *RERUN* in the console output, the HTML report and JUnit XML, and Allure lists the earlier attempts as retries. Review these after every nightly run; a test that needs a rerun regularly is flaky even though the build is green.
**Mitigation:** first read the trace and video of the failed attempt, then fix the cause instead of raising retries — replace timing assumptions with a condition to wait for, make the data unique, and remove shared state. Reruns are the safety net for a shared public demo, not the fix.

---

## 9. Key design decisions

- **Exactly 5 workflows (1 negative, 4 positive)**: one place for the lifecycle, no duplicated flows. Each is independent, so they parallelise and can be run alone.
- **Hybrid UI + API**: the UI is the source of truth; the API payloads are built from values read back from the UI, so the assertions link the two layers.
- **Validation as a layer, not as copy-paste**: `validate_response()` keeps the tests short and makes every API call be checked in the same complete way.
- **Data-driven**: employee data in JSON/CSV, API cases and expectations in `reqres_test_data.json`; the same file feeds k6, so the E2E suite and the load test cannot drift apart.
- **Performance separated from functional tests**: k6 is the right tool for load and thresholds; it has its own runner, its own CI job and its own report, and it does not consume the ReqRes quota of the functional runs.
- **Config through environment variables**: the same code runs locally, in GitHub Actions and in Jenkins.
- **ReqRes as the API layer**: the "API-level verification" step is simulated with the public ReqRes API (login, users), fed with the data read from the OrangeHRM UI. It is a shared public service with a small anonymous quota; use `REQRES_API_KEY` for regular runs.

---

## 10. Test data

- **`employees.json` / `.csv`:** `profile_picture` is uploaded when the employee is created and `edit_profile_picture` when it is edited (jpg, png or gif, up to 1 MB). The Employee Id and username get a random suffix at run time because the demo site is shared. The workflows use the first record.
- **`api/reqres_test_data.json`:** `auth_ui` (the wrong password for the negative workflow and the expected message), `auth_apis` (login and the "missing password" case with its expected status and error) and `user_apis` (request bodies, ids and expected status codes for POST / PUT / PATCH / DELETE). To test other values change the JSON, not the code.
- **Dropdown values:** `job_title` and `employment_status` must exist in the demo. If one is missing, the error message lists the available options.

---

## 11. UI locator map (from the application screenshots)

Most form fields are located by their **visible label**, using the `INPUT_BY_LABEL` and `SELECT_BY_LABEL` templates in `common_locators.py`. As a result, locator names read like the UI.

**Add Employee**: `AddEmployeeLocators`
| UI element | Locator name | Selector |
|---|---|---|
| First Name | `FIRST_NAME_INPUT` | `input[name='firstName']` |
| Middle Name | `MIDDLE_NAME_INPUT` | `input[name='middleName']` |
| Last Name | `LAST_NAME_INPUT` | `input[name='lastName']` |
| Employee Id | `EMPLOYEE_ID_INPUT` | input under the label "Employee Id" |
| Orange **+** on the avatar (opens the file chooser) | `ADD_PROFILE_PICTURE_BUTTON` | `button.employee-image-action` |
| Hidden photo file input (fallback) | `PROFILE_PICTURE_FILE_INPUT` | `input[type='file']` |
| Avatar preview | `PROFILE_PICTURE_PREVIEW` | `img.employee-image` |
| Create Login Details toggle | `CREATE_LOGIN_DETAILS_TOGGLE` | `div.oxd-switch-wrapper span.oxd-switch-input` |
| Username | `USERNAME_INPUT` | input under the label "Username" |
| Status Enabled / Disabled | `STATUS_ENABLED_RADIO` / `STATUS_DISABLED_RADIO` | the label "Enabled" / "Disabled" |
| Password / Confirm Password | `PASSWORD_INPUT` / `CONFIRM_PASSWORD_INPUT` | input under the matching label |
| Cancel / Save | `CANCEL_BUTTON` / `SAVE_BUTTON` | `button:has-text('Cancel')` / `button[type='submit']` |

**Personal Details**: `PersonalDetailsLocators`
| UI element | Locator name |
|---|---|
| Employee Id / Other Id | `EMPLOYEE_ID_INPUT` / `OTHER_ID_INPUT` |
| Driver's License Number / License Expiry Date | `DRIVERS_LICENSE_NUMBER_INPUT` / `LICENSE_EXPIRY_DATE_INPUT` |
| Nationality / Marital Status | `NATIONALITY_DROPDOWN` / `MARITAL_STATUS_DROPDOWN` |
| Gender Male / Female | `GENDER_MALE_RADIO` / `GENDER_FEMALE_RADIO` |
| Save (Personal Details) | `PERSONAL_DETAILS_SAVE_BUTTON` |

**Change Profile Picture**: `ChangeProfilePictureLocators`
| UI element | Locator name |
|---|---|
| "Change Profile Picture" title | `PAGE_TITLE` |
| Photo file input / preview | `PHOTO_FILE_INPUT` / `PHOTO_PREVIEW` |
| Save | `SAVE_BUTTON` |

**Contact Details**: `ContactDetailsLocators`
| UI element | Locator name |
|---|---|
| Street 1 / Street 2 / City | `STREET_1_INPUT` / `STREET_2_INPUT` / `CITY_INPUT` |
| State/Province / Zip / Country | `STATE_PROVINCE_INPUT` / `ZIP_POSTAL_CODE_INPUT` / `COUNTRY_DROPDOWN` |
| Telephone: Home / Mobile / Work | `HOME_TELEPHONE_INPUT` / `MOBILE_INPUT` / `WORK_TELEPHONE_INPUT` |
| Work Email / Other Email | `WORK_EMAIL_INPUT` / `OTHER_EMAIL_INPUT` |

**Job tab and Employee List**
| UI element | Locator name |
|---|---|
| Job Title / Employment Status dropdowns | `JobDetailsLocators.JOB_TITLE_DROPDOWN` / `EMPLOYMENT_STATUS_DROPDOWN` |
| Employee Id search box / Search button | `EmployeeListLocators.EMPLOYEE_ID_INPUT` / `SEARCH_BUTTON` |
| Result rows / cells / edit icon | `TABLE_ROWS` / `ROW_CELLS` / `ROW_EDIT_ICON` |

**Common** (every page): `CommonLocators` — top bar header (`MODULE_HEADER`), user menu (`USER_DROPDOWN`), side menu (`SIDE_MENU_ITEM`), PIM tabs (`TOP_NAV_TAB`), toasts (`TOAST_MESSAGE`), dropdown options (`DROPDOWN_OPTION`).

---

## 12. Dependencies

| Package | Purpose |
|---|---|
| `playwright` | Browser automation, API requests (`APIRequestContext`), video and tracing |
| `pytest` | Test runner |
| `pytest-playwright` | Browser fixtures and CLI options (`--browser`, `--headed`, `--slowmo`, `--browser-channel`) |
| `pytest-html` | Self-contained HTML report |
| `allure-pytest` | Allure results with steps and API attachments |
| `pytest-rerunfailures` | Retries for runs against the shared demo site |
| `pytest-xdist` | Parallel execution (`-n 2`) |
| `jsonschema` | Validating API responses against contracts |
| `PyYAML` | Reading the configuration file |
| `k6` (separate tool) | Performance test in `performance/k6/` |

---

## 13. Troubleshooting

| Symptom | Fix |
|---|---|
| `Login rejected with 'Invalid credentials'` for `Admin` | The public demo's password is sometimes changed or reset by other users. Check the current credentials on the demo login page and set `ORANGEHRM_USERNAME` / `ORANGEHRM_PASSWORD`. |
| `pytest.exe ... blocked by Application Control policy` | Use `python -m pytest`. |
| `run_tests.bat` / `run_tests.sh` "not recognized" (PowerShell) | Use `.\run_tests.bat ...` — PowerShell doesn't run scripts from the current folder without the `.\` prefix. |
| `choco : not recognized` | Chocolatey isn't installed. Use `winget install k6 --source winget` instead, or the direct `.msi` installer. |
| `k6 : not recognized` right after `winget install k6` | winget updated PATH for **new** terminal sessions only. Close every open terminal and open a fresh one. If it's still not found, run `[Environment]::SetEnvironmentVariable('Path', $env:Path + ';C:\Program Files\k6', 'User')`, then reopen the terminal again (`setx` truncates long PATH values — avoid it for this). |
| ReqRes returns **401** or **403** | ReqRes may require a key. Create a free one at app.reqres.in and set `REQRES_API_KEY` (`python tools/check_reqres.py` tests it). |
| ReqRes returns **429** "demo limit of 40 requests/day" | The anonymous daily quota is used up (resets at midnight UTC). Set `REQRES_API_KEY`, or `REQRES_SKIP_ON_QUOTA=true` to report the API step as skipped. |
| k6: `could not write report ... no such file or directory` | Create the folder first: `mkdir reports\performance` (PowerShell) — `run_tests.bat perf` and CI do it automatically. |
| k6: many `HTTP 429` and failed thresholds | The free ReqRes tier is rate-limited. Use the `smoke` profile or set `REQRES_API_KEY`. |
| "Add Employee title should be visible" / test lands back on the login page | The demo site's SPA can still be mid-render right after login. Handled by `DashboardPage.verify_loaded()` waiting for network-idle + widgets before the next click; if it still happens occasionally, raise `EXPECT_TIMEOUT`/`DEFAULT_TIMEOUT` or add `--reruns`. |
| `Option 'QA Engineer' is not available` | The shared demo data changed. Use one of the options listed in the error. |
| Debugging a UI failure | `python -m playwright show-trace reports/traces/<test>.zip` |

---

## 14. Observations (Part 6 – Reporting & Observability)

- **HTML report** (`pytest-html`, `--self-contained-html`) is a single portable file with pass/fail/rerun status, full log output, and embedded failure screenshot + linked failure video — easiest artifact to share as-is.
- **Videos are recorded for every test, not just failures** — for a slow-page issue, the video of a *passing* test still shows exactly where the wait happened, not only failures. Screenshot answers "what did the final state look like," video answers "what led up to it," and the Playwright trace (`retain-on-failure`) answers "what was the network/DOM doing" — keeping all three together is what made a subtle post-login race condition (a loading-skeleton username being asserted as real) diagnosable at all.
- **Tags are orthogonal, not hierarchical** — a test can be `workflow` + `positive` + `smoke` simultaneously, letting CI run a fast gate (`smoke`) on every push and reserve `regression` for nightly, without duplicating test files.
- **Environment-based execution** means the same test code runs unmodified against local, staging, or CI by only changing environment variables (`ORANGEHRM_BASE_URL`, timeouts, etc.) — no code branching per environment.
- **Retry logic has two independent layers, and they show up differently in reports:**
  - Test-level (`--reruns=2 --reruns-delay=3` in `pytest.ini`) — a full test re-execution, visible as `RERUN` in the HTML report and JUnit XML, with its own fresh screenshot/video/trace per attempt. Note: `--reruns` must actually be set — `--rerun-except` alone filters *which* failures get retried but enables nothing by itself.
  - Navigation-level (`base_page.py::navigate()` retrying one `page.goto()` timeout) — invisible in the HTML report; only visible via the log line `Navigation to ... timed out once - retrying`. Worth grepping logs for this after a run to see how often it's firing, separate from full-test reruns.
- **Recommendation for ongoing observability:** track `RERUN` occurrences in `results.xml` per nightly run over time. A test that reruns occasionally is absorbing genuine shared-demo flakiness; one that reruns on *every* run is a real bug wearing a retry as a bandage and should be investigated via its trace/video rather than papered over with more reruns.