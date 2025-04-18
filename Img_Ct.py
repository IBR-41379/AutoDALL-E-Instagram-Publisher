import json
import os
import time
import requests
from openai import OpenAI

CONFIG_FILE = "dalle_config.json"

DEFAULT_CONFIG = {
    "use_config": False,
    "style": "vivid",
    "model": "dall-e-3",
    "size": "1024x1024",
    "quality": "hd"
}

RESOLUTIONS = [
    {"size": "256x256", "models": ["dall-e-2"]},
    {"size": "512x512", "models": ["dall-e-2"]},
    {"size": "1024x1024", "models": ["dall-e-2", "dall-e-3"]},
    {"size": "1024x1792", "models": ["dall-e-3"]},
    {"size": "1792x1024", "models": ["dall-e-3"]},
]

STYLES = ["vivid", "natural"]
QUALITIES = ["standard", "hd"]

# client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def create_default_config():
    """Create default config file if missing"""
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        print(f"Created default config: {CONFIG_FILE}")


def load_config():
    """Load and validate configuration file"""
    create_default_config()  # Ensure config exists
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        # Validate config structure
        if not all(key in config for key in DEFAULT_CONFIG):
            print("Invalid config structure, using defaults")
            return DEFAULT_CONFIG
        # Validate model/size compatibility
        valid_size = any(
            res["size"] == config["size"] and config["model"] in res["models"]
            for res in RESOLUTIONS
        )
        return config if valid_size else DEFAULT_CONFIG
    except Exception as e:
        print(f"Error loading config: {str(e)}, using defaults")
        return DEFAULT_CONFIG


def print_numbered_options(items, title=None):
    """Helper function to print numbered options"""
    if title:
        print(f"\n{title}:")
    for i, item in enumerate(items, 1):
        print(f"{i}. {item.capitalize() if isinstance(item, str) else item}")


def get_user_choice(options, title, error_msg="Invalid choice"):
    """Get validated numbered choice from user"""
    while True:
        print_numbered_options(options, title)
        try:
            choice = int(input(f"Enter choice (1-{len(options)}): "))
            if 1 <= choice <= len(options):
                return choice  # Return numerical choice
            raise ValueError
        except (ValueError, IndexError):
            print(f"{error_msg}. Please try again.")


def collect_interactive_input():
    """Interactive input collection"""
    params = {
        "prompt": input("Enter your image prompt: "),
        "style": None,
        "model": None,
        "size": None,
        "quality": "standard"
    }
    # Style selection
    style_choice = get_user_choice(STYLES, "Select Style")
    params["style"] = STYLES[style_choice - 1]
    # Resolution and model selection
    res_options = [
        f"{res['size']} ({'/'.join(res['models'])})" for res in RESOLUTIONS]
    res_choice = get_user_choice(res_options, "Select Resolution")
    selected_res = RESOLUTIONS[res_choice - 1]
    if len(selected_res["models"]) > 1:
        model_choice = get_user_choice(selected_res["models"], "Select Model")
        params["model"] = selected_res["models"][model_choice - 1]
    else:
        params["model"] = selected_res["models"][0]
    params["size"] = selected_res["size"]
    # Quality selection for DALL-E 3
    if params["model"] == "dall-e-3":
        quality_choice = get_user_choice(QUALITIES, "Select Quality")
        params["quality"] = QUALITIES[quality_choice - 1]
    return params


def get_user_input():
    """Get parameters based on config preference"""
    config = load_config()
    if config.get("use_config", True):
        print("\nUsing settings from config file:")
        print(f"Model: {config['model']}")
        print(f"Size: {config['size']}")
        print(f"Style: {config['style']}")
        print(f"Quality: {config['quality']}")
        return {
            "prompt": input("\nEnter your image prompt: "),
            "style": config["style"],
            "model": config["model"],
            "size": config["size"],
            "quality": config["quality"]
        }
    # Fallback to interactive input
    print("\nConfig usage disabled, entering interactive mode:")
    return collect_interactive_input()


def generate_image(params):
    """Generate and save image using OpenAI API"""
    try:
        generation_args = {
            "model": params["model"],
            "prompt": params["prompt"],
            "size": params["size"],
            "n": 1,
            "response_format": "url"
        }
        if params["model"] == "dall-e-3":
            generation_args.update({
                "style": params["style"],
                "quality": params["quality"]
            })
        response = client.images.generate(**generation_args)
        image_url = response.data.url
        os.makedirs("images", exist_ok=True)
        timestamp = int(time.time())
        # Sanitize prompt and style for filename
        def sanitize(text):
            return "".join(c for c in text if c.isalnum() or c in (' ', '_')).rstrip().replace(' ', '_')
        prompt_safe = sanitize(params["prompt"][:50])  # limit length for filename
        style_safe = sanitize(params["style"])
        filename = f"images/dalle_{prompt_safe}_{style_safe}_{timestamp}.png"
        image_data = requests.get(image_url, timeout=30).content
        with open(filename, "wb") as f:
            f.write(image_data)
        return filename
    except Exception as e:
        print(f"\nError generating image: {str(e)}")
        return None

if __name__ == "__main__":
    print("=== DALL·E Image Generator ===")
    while True:
        params = get_user_input()
        filename = generate_image(params)
        if filename:
            print(f"\nSuccess! Image saved as: {filename}")
        else:
            print("\nFailed to generate image. Please check your inputs.")
        if input("\nGenerate another image? (y/n): ").lower() != 'y':
            break
