"""Provide branding (customizing text) to Shawl."""

import json
import pathlib

import dataclasses


@dataclasses.dataclass
class Brand:
    """Class passed to shawl to customize its apperance and or functionality."""

    name: str

    app_name: str
    page_title: str

    hostname_label: str
    hostname_value: str
    username_label: str
    password_label: str
    local_path_label: str
    remote_path_label: str

    upload_button_text: str
    run_button_text: str
    watch_queue_button_text: str
    remote_shell_button_text: str
    download_button_text: str
    file_browser_button_text: str

    manual_file: str


def load_brands():
    """Load brands from brand/*.json files."""
    brand_files = pathlib.Path("brands").glob("*.json")
    ret = dict()
    for brand_file in brand_files:
        with open(brand_file) as b_fd:
            brand_json = json.load(b_fd)
            brand = Brand(**brand_json)
            ret[brand.name] = brand
    return ret


if __name__ == "__main__":
    print(load_brands().values())
