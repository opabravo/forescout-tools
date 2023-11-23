import time
import json
import yaml
import sys
from forescout import Admin, WebAPI
from forescout.constant import Settings, FunctionRequiredFields
from forescout.utils.log import get_logger
from pathlib import Path
from deepdiff import DeepDiff


logger = get_logger()

# Get current working directory based on script or frozen exe
if getattr(sys, 'frozen', False):
    CWD = Path(sys.executable).parent
else:
    CWD = Path(__file__).parent


def load_config() -> Settings:
    config_file = CWD / "config.yaml"
    if not config_file.exists():
        logger.error(f"[-] Config file not found: {config_file}")
        return

    with open(config_file, "r") as f:
        data = yaml.safe_load(f)
        if not data:
            logger.error(f"[-] Config file is empty: {config_file}")
            return
        config = Settings(**data)

    return config

def save_config(config: Settings):
    config_file = CWD / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config.__dict__, f, default_flow_style=False)
    logger.info(f"Saved to: {config_file.resolve()} (To change your settings, edit this file.")

def get_function_required_fields(function_type: str):
    required_fields = ["FS_URL"]

    if function_type == "admin":
        required_fields.extend(FunctionRequiredFields().admin)
    elif function_type == "web":
        required_fields.extend(FunctionRequiredFields().web)

    return required_fields
    

def check_config(config: Settings, function_type: str) -> bool:
    """Check if config file has all required fields"""
    required_fields = get_function_required_fields(function_type)
    fields_not_set = []
    for field in required_fields:
        value = getattr(config, field, None)
        if not value:
            fields_not_set.append(field)
            continue

    if not fields_not_set:
        return True

    logger.error(f"[-] config.yaml The following parameters are missing: {fields_not_set}")
    return False

def prompt_config(function_type: str, previos_config: Settings) -> dict:
    """Prompt user to input config data and save it to config.yaml"""
    required_fields = get_function_required_fields(function_type)
    config = Settings()
    if previos_config:
        config = previos_config

    for field in required_fields:
        value = getattr(config, field, None)
        if value:
            continue
        
        while True:
            value = input(f"Please enter {field} -> ")
            if not value:
                logger.error("[-] Do not enter a null value")
                continue
            setattr(config, field, value)
            break

    save_config(config)
    return config


# def check_settings(fields: set):
#     fields_not_set = []
#     for field in fields:
#         value = getattr(settings, field, None)
#         if not value:
#             fields_not_set.append(field)
#             continue

#     if not fields_not_set:
#         return True

#     logger.error(f"[-] Please set the following parameters: {fields_not_set} in .env file first")
#     return False


@logger.catch
def edit_segments():
    # Check settings file
    config = load_config()
    config_check = check_config(config, "admin")
    if not config_check:
        config = prompt_config("admin", config)
    admin = Admin(config.FS_URL, config.FS_ADMIN_USERNAME, config.FS_ADMIN_PASSWORD)
    # if not check_settings({"FS_URL", "FS_ADMIN_USERNAME", "FS_ADMIN_PASSWORD"}):
    #     return

    # Init admin
    # admin = Admin(settings.FS_URL, settings.FS_ADMIN_USERNAME, settings.FS_ADMIN_PASSWORD)
    logger.info("Logging in...")
    is_success = admin.login()
    if not is_success:
        logger.error("Login failed")
        return

    logger.success("Login sucessful")

    # time.sleep(3)
    # segments = admin.fetch_segments()
    # logger.info(f"Segments: {segments}")

    # Backup segments
    logger.info("Backing upSegments...")
    time.sleep(3)
    backup_file_path_str = admin.backup_segments()
    backup_file_path = Path(backup_file_path_str)
    logger.info(f"Backed up: {backup_file_path.resolve()}")


    # Copy the backup file to segments folder
    # segments_folder = CWD / "segments"
    # shutil.copy(backup_file_path, segments_folder)
    # segment_file_path = segments_folder / backup_file_path.name
    # logger.info(f"Copied to: {segments_folder.resolve()}")

    # while 1:
    #     logger.info(f"\nPlease change {segment_file_path.resolve()} Archival Content")
    #     input("Press Enter to go on...")
    #     try:
    #         with open(segment_file_path, "r") as f:
    #             loaded_segments = json.load(f)
    #             segments_to_update = loaded_segments["node"]
    #     except json.decoder.JSONDecodeError as e:
    #         logger.error(f"[-] The JSON Format is wrong: {e}")
    #         logger.exception(e)
    #     except KeyError as e:
    #         logger.error(f"[-] Bad Forescout Segments JSON file with missing {e} field")
    #         logger.exception(e)
    #     except Exception as e:
    #         logger.error(f"[-] File read error: {e}")
    #         logger.exception(e)
    #     else:
    #         break

    while 1:
        segment_file = input("\nPlease drag After the change, the JSON file is here -> ")
        if not segment_file:
            logger.error("[!] Please enter the file path")
            continue

        segment_file_path = Path(segment_file.strip('"').strip("'"))

        if not segment_file_path.exists():
            logger.error(f"[-] The archive does not exist: {segment_file}")
            continue

        if not str(segment_file_path).lower().endswith(".json"):
            logger.error("[!] Please enter the JSON file")
            continue

        # segment_file = "./backups/original_segments.json"
        # Prompt user to edit json file
        try:
            with open(segment_file_path, "r") as f:
                loaded_segments = json.load(f)
                segments_to_update = loaded_segments["node"]
        except json.decoder.JSONDecodeError as e:
            logger.error(f"[-] JSON Format Error: {e}")
            logger.exception(e)
        except KeyError as e:
            logger.error(f"[-] Bad Forescout Segments JSON file with missing {e} field")
            logger.exception(e)
        except Exception as e:
            logger.error(f"[-] File read error: {e}")
            logger.exception(e)
        else:
            break

    # Compare the difference between segments
    with open(backup_file_path, "r") as f:
        original_segments = json.load(f)["node"]

    segments_diff = DeepDiff(original_segments, segments_to_update, ignore_order=True)
    # Prettify the segments diff in json
    segments_diff_parsed = json.dumps(segments_diff, indent=4)

    # Make sure the segments is in json format for web trnasfer
    # logger.warning(f"\n[*] This setting overrides the current Segments setting:\n {segments_to_update}")
    logger.warning(f"\n[*] Segments differences:\n---\n{segments_diff_parsed}\n---\n")
    # print(json.dumps(segments_diff, indent=4))
    confirm = input("\n[!] Check whether you want to update segments (Y/N) -> ")

    if confirm.lower() not in {"y", "yes"}:
        logger.info("[-] The user cancels updating segments")
        return

    time.sleep(3)


    response = admin.update_segments(segments_to_update)
    if response.status_code == 200:
        logger.success("[+] Segments updated successfully")
    else:
        logger.error(f"[!] Update failure: {response.text}")

@logger.catch
def web_api_utils():
    # Check settings
    config = load_config()
    config_check = check_config(config, "web")
    if not config_check:
        config = prompt_config("web", config)
    web = WebAPI(config.FS_URL, config.FS_WEB_USERNAME, config.FS_WEB_PASSWORD)
    # if not check_settings({"FS_URL", "FS_WEB_USERNAME", "FS_WEB_PASSWORD"}):
        # return
    
    # web = WebAPI(settings.FS_URL, settings.FS_WEB_USERNAME, settings.FS_WEB_PASSWORD)
    logger.info("Logging in...")
    is_success = web.login()
    if not is_success:
        logger.error("Login failed")
        return
    
    logger.success("Login successful")
    # logger.info("All network devices are being acquired...")
    # hosts = web.fetch_hosts()

    # Backup Hosts
    logger.info("Backing up network devices...")
    backup_file_path_str = web.backup_hosts(CWD / "hosts")
    backup_file_path = Path(backup_file_path_str)
    logger.info(f"Backed up to: {backup_file_path.resolve()}")


def show_banner():
    print("""
------------------------------------------------------------------------
 ___ __  ___ ___  __   ___ __  _  _ _____   _____ __   __  _    __  
| __/__\| _ \ __/' _/ / _//__\| || |_   _| |_   _/__\ /__\| | /' _/ 
| _| \/ | v / _|`._`.| \_| \/ | \/ | | |     | || \/ | \/ | |_`._`. 
|_| \__/|_|_\___|___/ \__/\__/ \__/  |_|     |_| \__/ \__/|___|___/ 

Forescout API - Segments management tool

                  @2023 by - https://github.com/opabravo/forescout-tools
------------------------------------------------------------------------
    """)


def init():
    """Some initialization upon program start"""
    # Check if required folders exist
    for folder in {"backups", "segments", "hosts"}:
        path = Path(CWD / folder)
        if not path.exists():
            path.mkdir()
            logger.info(f"The {folder} folder has been created...")

    return True

def main():
    while 1:
        print("""
[1] Update Segments
[2] Web API Utils
[3] Exit
        """)
        choice = input("Please select -> ")
        if choice == "1":
            edit_segments()
        elif choice == "2":
            web_api_utils()
        elif choice == "3":
            break
        else:
            logger.warning("[-] Please enter a valid option")


if __name__ == "__main__":
    show_banner()

    logger.info("Initialize...")
    init_result = init()
    if not init_result:
        logger.error("Initialization failed")
        input("Press any key to finish...")
        exit()

    try:
        main()
    except KeyboardInterrupt:
        logger.error("\n[-] The user interrupts the program")
    input("Press any key to finish...")
