import os
import time
import requests
from openai import OpenAI
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread
from pyngrok import ngrok

# Configuration
CONFIG = {
    'endpoint_base': 'https://graph.facebook.com/v19.0/',
    'instagram_account_id': 'YOUR_INSTAGRAM_BUSINESS_ACCOUNT_ID',
    'access_token': 'YOUR_LONG_LIVED_ACCESS_TOKEN',
    'media_type': 'IMAGE',
    'upload_delay': 10  # Seconds between posts to avoid rate limits
}

def get_image_files(directory="images"):
    """Get all unprocessed DALL-E generated images"""
    processed_dir = os.path.join(directory, "processed")
    os.makedirs(processed_dir, exist_ok=True)
    
    images = []
    for filename in os.listdir(directory):
        if (filename.startswith("dalle_") 
            and filename.lower().endswith(('.png', '.jpg', '.jpeg'))
            and not os.path.exists(os.path.join(processed_dir, filename))):
            images.append(os.path.join(directory, filename))
            
    return sorted(images)  # Sort by creation time via filename timestamp

def generate_instagram_caption(image_filename):
    """Extract prompt/style from filename and generate caption"""
    try:
        base_name = os.path.splitext(os.path.basename(image_filename))[0]
        parts = base_name.split('_')
        
        # Format: dalle_{prompt_parts}_{style}_{timestamp}
        style = parts[-2]
        prompt_parts = parts[1:-2]  # All parts between 'dalle' and style
        prompt = ' '.join(prompt_parts).replace('_', ' ')
        
    except Exception as e:
        raise ValueError(f"Filename format error: {str(e)}")
    
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{
            "role": "user",
            "content": f"""
            Create Instagram caption for AI art with:
            - Prompt: "{prompt}"
            - Style: "{style}"
            - 5-7 emojis
            - 3-5 hashtags
            - Mysterious tone
            - <220 characters
            - No markdown
            """
        }]
    )
    
    return response.choices[0].message.content.strip()

def start_local_server(image_dir, port=8000):
    """Start HTTP server and ngrok tunnel"""
    os.chdir(image_dir)
    server = HTTPServer(('', port), SimpleHTTPRequestHandler)
    Thread(target=server.serve_forever, daemon=True).start()
    return server, ngrok.connect(port, "http").public_url

def create_media_container(params, image_url):
    """Create Instagram media container"""
    url = f"{params['endpoint_base']}{params['instagram_account_id']}/media"
    response = requests.post(url, params={
        'caption': params['caption'],
        'access_token': params['access_token'],
        'image_url': image_url
    })
    response.raise_for_status()
    return response.json()['id']

def publish_media(container_id, params):
    """Publish media container to Instagram"""
    url = f"{params['endpoint_base']}{params['instagram_account_id']}/media_publish"
    response = requests.post(url, params={
        'creation_id': container_id,
        'access_token': params['access_token']
    })
    response.raise_for_status()
    return response.json()

def process_image(image_path, public_url):
    """Full processing pipeline for a single image"""
    try:
        # 1. Prepare paths
        image_dir = os.path.dirname(image_path)
        filename = os.path.basename(image_path)
        image_url = f"{public_url}/{filename}"
        
        # 2. Generate caption
        try:
            caption = generate_instagram_caption(filename)
            print(f"\nCaption for {filename}:\n{caption}")
        except Exception as e:
            print(f"Caption generation failed: {str(e)}")
            caption = "AI-generated artwork #DigitalArt #AICreativity"
        
        # 3. Create media container
        container_id = create_media_container(CONFIG, image_url)
        print(f"Container ID: {container_id}")
        
        # 4. Wait for processing
        print("Checking media status...")
        start_time = time.time()
        while True:
            status_response = requests.get(
                f"{CONFIG['endpoint_base']}{container_id}",
                params={'fields': 'status_code', 'access_token': CONFIG['access_token']}
            )
            status = status_response.json().get('status_code')
            
            if status == 'FINISHED':
                break
            if status in ('ERROR', 'EXPIRED'):
                raise Exception(f"Media processing failed: {status}")
            if time.time() - start_time > 300:  # 5-minute timeout
                raise TimeoutError("Media processing timed out")
                
            time.sleep(5)
        
        # 5. Publish post
        result = publish_media(container_id, CONFIG)
        print(f"Published post ID: {result.get('id')}")
        
        # 6. Move to processed
        processed_dir = os.path.join(image_dir, "processed")
        os.makedirs(processed_dir, exist_ok=True)
        os.rename(image_path, os.path.join(processed_dir, filename))
        
        return True
        
    except Exception as e:
        print(f"Failed to process {filename}: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        # 1. Get images to process
        image_files = get_image_files()
        if not image_files:
            print("No images found in 'images' directory")
            exit()
            
        print(f"Found {len(image_files)} images to upload:")
        for img in image_files:
            print(f" - {os.path.basename(img)}")
        
        # 2. Start file server
        server, public_url = start_local_server("images")
        print(f"\nPublic URL: {public_url}")
        
        # 3. Process images
        success_count = 0
        failed_files = []
        
        for idx, image_path in enumerate(image_files, 1):
            print(f"\n{'='*50}")
            print(f"Processing {idx}/{len(image_files)}: {os.path.basename(image_path)}")
            
            if process_image(image_path, public_url):
                success_count += 1
                if idx < len(image_files):
                    print(f"Waiting {CONFIG['upload_delay']}s before next upload...")
                    time.sleep(CONFIG['upload_delay'])
            else:
                failed_files.append(os.path.basename(image_path))
        
        # 4. Print summary
        print(f"\n{'='*50}")
        print(f"Successfully uploaded: {success_count}/{len(image_files)}")
        if failed_files:
            print(f"Failed files:")
            for f in failed_files:
                print(f" - {f}")
                
    except Exception as e:
        print(f"Critical error: {str(e)}")
    finally:
        print("\nCleaning up resources...")
        ngrok.kill()
        if 'server' in locals():
            server.shutdown()