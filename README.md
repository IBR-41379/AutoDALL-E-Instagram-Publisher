# AutoDALL-E-Instagram-Publisher
*A seamless pipeline for AI image generation and social media publishing*

---

## 📖 README

### **Project Overview**  
This project provides a two-part system for AI-powered content creation:
1. **`Img_ct.py`**: Generates images using OpenAI's DALL-E 3/2 based on user prompts.  
2. **`Insta_img.py`**: Automatically posts generated images to Instagram with AI-generated captions.  

---

## 🚀 Key Features  
- **AI Image Generation**  
  - Supports DALL-E 3 (HD/Standard) and DALL-E 2  
  - Configurable resolution, style, and quality  
- **Smart Instagram Integration**  
  - Auto-captioning using GPT-4  
  - Batch uploading of generated images  
  - Rate limit management  
- **File Management**  
  - Unique filenames with prompt/style metadata  
  - Automatic organization into `processed/` directory  

---

## ⚙️ Prerequisites  
1. **Accounts**  
   - OpenAI API key (for DALL-E and GPT-4)  
   - Instagram Business/Creator account  
   - Facebook Developer account with Graph API access  
2. **Software**  
   - Python 3.8+  
   - Ngrok (for local tunneling)  

---

## 🛠️ Installation  
```bash
git clone https://github.com/IBR-41379/AutoDALL-E-Instagram-Publisher.git
cd AutoDALL-E-Instagram-Publisher
pip install openai requests pyngrok python-dotenv
```

---

## 🔧 Configuration  

### 1. Environment Variables  
Create `.env` file:  
```ini
OPENAI_API_KEY=your_openai_key_here
INSTAGRAM_ACCOUNT_ID=your_ig_business_id
FACEBOOK_ACCESS_TOKEN=your_long_lived_token
```

### 2. File Structure  
```
project-root/
├── images/           # Generated images
├── processed/        # Successfully posted images
├── Img_ct.py         # Image generation script
├── Insta_img.py      # Instagram upload script
└── dalle_config.json # Configuration file
```

---

## 🖼️ Image Generation (Img_ct.py)  

### Usage  
```bash
python Img_ct.py
```
**Workflow**:  
1. Configure settings via interactive menu  
2. Generates images to `images/` directory  
3. Filename format: `dalle_{prompt}_{style}_{timestamp}.png`

---

## 📤 Instagram Upload (Insta_img.py)  

### Usage  
```bash
python Insta_img.py
```
**Automated Process**:  
1. Scans `images/` directory  
2. Generates captions using GPT-4  
3. Posts images via Instagram Graph API  
4. Moves processed files to `images/processed/`  

---

## ⚠️ Important Notes  

1. **Instagram Limits**  
   - Max 25 posts/day via Graph API  
   - Images must be JPEG/PNG with aspect ratio between 4:5 and 1.91:1  

2. **Filename Requirements**  
   - Follow strict format: `dalle_{prompt}_{style}_{timestamp}.png`  
   - Example: `dalle_A_cosmic_cat_vivid_1716234567.png`  

3. **Ngrok Considerations**  
   - Free tier has limited tunnel duration  
   - For production, use permanent hosting instead  

---
