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
    logger.info(f"已儲存至: {config_file.resolve()}，欲更改設定請編輯此檔案!")

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

    logger.error(f"[-] config.yaml 缺乏以下參數: {fields_not_set}")
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
            value = input(f"請輸入 {field} -> ")
            if not value:
                logger.error("[-] 請勿輸入空值")
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

#     logger.error(f"[-] 請先至 .env 設定以下參數: {fields_not_set}")
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
    logger.info("正在登入...")
    is_success = admin.login()
    if not is_success:
        logger.error("登入失敗")
        return

    logger.success("登入成功")

    # time.sleep(3)
    # segments = admin.fetch_segments()
    # logger.info(f"Segments: {segments}")

    # Backup segments
    logger.info("正在備份Segments...")
    time.sleep(3)
    backup_file_path_str = admin.backup_segments()
    backup_file_path = Path(backup_file_path_str)
    logger.info(f"已備份到: {backup_file_path.resolve()}")


    # Copy the backup file to segments folder
    # segments_folder = CWD / "segments"
    # shutil.copy(backup_file_path, segments_folder)
    # segment_file_path = segments_folder / backup_file_path.name
    # logger.info(f"已複製到: {segments_folder.resolve()}")

    # while 1:
    #     logger.info(f"\n請更改 {segment_file_path.resolve()} 檔案內容")
    #     input("按下Enter繼續...")
    #     try:
    #         with open(segment_file_path, "r") as f:
    #             loaded_segments = json.load(f)
    #             segments_to_update = loaded_segments["node"]
    #     except json.decoder.JSONDecodeError as e:
    #         logger.error(f"[-] JSON格式錯誤: {e}")
    #         logger.exception(e)
    #     except KeyError as e:
    #         logger.error(f"[-] 錯誤的Forescout Segments JSON檔，缺少 {e} 欄位")
    #         logger.exception(e)
    #     except Exception as e:
    #         logger.error(f"[-] 檔案讀取錯誤: {e}")
    #         logger.exception(e)
    #     else:
    #         break

    while 1:
        segment_file = input("\n請拖曳 更改後JSON檔到此 -> ")
        if not segment_file:
            logger.error("[!] 請輸入檔案路徑")
            continue

        segment_file_path = Path(segment_file.strip('"').strip("'"))

        if not segment_file_path.exists():
            logger.error(f"[-] 檔案不存在: {segment_file}")
            continue

        if not str(segment_file_path).lower().endswith(".json"):
            logger.error("[!] 請輸入JSON檔")
            continue

        # segment_file = "./backups/original_segments.json"
        # Prompt user to edit json file
        try:
            with open(segment_file_path, "r") as f:
                loaded_segments = json.load(f)
                segments_to_update = loaded_segments["node"]
        except json.decoder.JSONDecodeError as e:
            logger.error(f"[-] JSON格式錯誤: {e}")
            logger.exception(e)
        except KeyError as e:
            logger.error(f"[-] 錯誤的Forescout Segments JSON檔，缺少 {e} 欄位")
            logger.exception(e)
        except Exception as e:
            logger.error(f"[-] 檔案讀取錯誤: {e}")
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
    # logger.warning(f"\n[*] 此設定將覆蓋目前的Segments設定:\n {segments_to_update}")
    logger.warning(f"\n[*] Segments差異:\n---\n{segments_diff_parsed}\n---\n")
    # print(json.dumps(segments_diff, indent=4))
    confirm = input("\n[!] 請確認是否要更新Segments (Y/N) -> ")

    if confirm.lower() not in {"y", "yes"}:
        logger.info("[-] 使用者取消更新Segments")
        return

    time.sleep(3)


    response = admin.update_segments(segments_to_update)
    if response.status_code == 200:
        logger.success("[+] 成功更新Segments")
    else:
        logger.error(f"[!] 更新失敗: {response.text}")

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
    logger.info("正在登入...")
    is_success = web.login()
    if not is_success:
        logger.error("登入失敗")
        return
    
    logger.success("登入成功")
    # logger.info("正在取得所有網路設備...")
    # hosts = web.fetch_hosts()

    # Backup Hosts
    logger.info("正在備份網路設備...")
    backup_file_path_str = web.backup_hosts(CWD / "hosts")
    backup_file_path = Path(backup_file_path_str)
    logger.info(f"已備份到: {backup_file_path.resolve()}")


def show_banner():
    print("""
------------------------------------------------------------------------
 ___ __  ___ ___  __   ___ __  _  _ _____   _____ __   __  _    __  
| __/__\| _ \ __/' _/ / _//__\| || |_   _| |_   _/__\ /__\| | /' _/ 
| _| \/ | v / _|`._`.| \_| \/ | \/ | | |     | || \/ | \/ | |_`._`. 
|_| \__/|_|_\___|___/ \__/\__/ \__/  |_|     |_| \__/ \__/|___|___/ 

Forescout API - Segments管理工具

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
            logger.info(f"已建立 {folder} 資料夾...")

    return True

def main():
    while 1:
        print("""
[1] 更新Segments
[2] Web API Utils
[3] 離開
        """)
        choice = input("請選擇 -> ")
        if choice == "1":
            edit_segments()
        elif choice == "2":
            web_api_utils()
        elif choice == "3":
            break
        else:
            logger.warning("[-] 請輸入有效選項")


if __name__ == "__main__":
    show_banner()

    logger.info("初始化...")
    init_result = init()
    if not init_result:
        logger.error("初始化失敗")
        input("按任意鍵結束...")
        exit()

    try:
        main()
    except KeyboardInterrupt:
        logger.error("\n[-] 使用者中斷程式")
    input("按任意鍵結束...")