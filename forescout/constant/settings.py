from dataclasses import dataclass, field


@dataclass
class Settings:
    FS_URL: str = ""
    FS_ADMIN_USERNAME: str = ""
    FS_ADMIN_PASSWORD: str = ""
    FS_WEB_USERNAME: str = ""
    FS_WEB_PASSWORD: str = ""

@dataclass
class FunctionRequiredFields:
    admin: list = field(init=False, default_factory=lambda: ["FS_ADMIN_USERNAME", "FS_ADMIN_PASSWORD"])
    web: list =  field(init=False, default_factory=lambda: ["FS_WEB_USERNAME", "FS_WEB_PASSWORD"])