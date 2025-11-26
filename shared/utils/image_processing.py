import os
import numpy as np
from PIL import Image,ImageEnhance,ImageFilter
import logging
logger=logging.getLogger(__name__)
BRIGHTNESS_THRESHOLD,CONTRAST_THRESHOLD=100,40
def load_and_validate_image(image_path:str)->Image.Image:
    try:
        if not os.path.exists(image_path):raise FileNotFoundError(f"Image file not found: {image_path}")
        if not os.access(image_path,os.R_OK):raise PermissionError(f"Cannot read image file: {image_path}")
        file_size=os.path.getsize(image_path)
        if file_size==0:raise ValueError(f"Image file is empty: {image_path}")
        logger.info(f"Loading image from: {image_path} (size: {file_size} bytes)")
        image=Image.open(image_path)
        if image is None:raise ValueError(f"PIL failed to load image: {image_path}")
        if image.mode not in('RGB','L'):
            if image.mode=='RGBA':
                background=Image.new('RGB',image.size,(255,255,255))
                background.paste(image,mask=image.split()[3])
                image=background
            else:image=image.convert('RGB')
        logger.info(f"Loaded image successfully: {image.size[0]}x{image.size[1]}")
        return image
    except Exception as e:
        logger.error(f"Failed to load image from {image_path}: {e}")
        raise
def enhance_image(image:Image.Image,enhance_contrast:bool=True,enhance_brightness:bool=True,sharpen:bool=True)->Image.Image:
    try:
        enhanced=image.copy()
        if enhance_brightness:
            enhancer=ImageEnhance.Brightness(enhanced)
            enhanced=enhancer.enhance(1.2)
        if enhance_contrast:
            enhancer=ImageEnhance.Contrast(enhanced)
            enhanced=enhancer.enhance(1.3)
        if sharpen:enhanced=enhanced.filter(ImageFilter.SHARPEN)
        logger.info("Image enhancement applied")
        return enhanced
    except Exception as e:
        logger.warning(f"Enhancement failed, using original: {e}")
        return image
def assess_image_quality(image:Image.Image)->dict:
    try:
        img_array=np.array(image.convert('L'))
        brightness,contrast=np.mean(img_array),np.std(img_array)
        quality={'brightness':float(brightness),'contrast':float(contrast),'is_bright_enough':brightness>BRIGHTNESS_THRESHOLD,'has_good_contrast':contrast>CONTRAST_THRESHOLD,'overall_quality':'good'if(brightness>BRIGHTNESS_THRESHOLD and contrast>CONTRAST_THRESHOLD)else'poor'}
        logger.info(f"Image quality: brightness={brightness:.1f}, contrast={contrast:.1f}")
        return quality
    except Exception as e:
        logger.error(f"Quality assessment failed: {e}")
        return{'overall_quality':'unknown'}
def preprocess_for_ocr(image:Image.Image,aggressive:bool=True)->Image.Image:
    import cv2
    try:
        img_array=np.array(image)
        if img_array is None or img_array.size==0:raise ValueError("Image array is empty or None")
        logger.info(f"Image array shape: {img_array.shape}")
        if len(img_array.shape)==3:gray=cv2.cvtColor(img_array,cv2.COLOR_RGB2GRAY)
        else:gray=img_array
        if aggressive:
            height,width=gray.shape
            if max(height,width)<1000:
                scale_factor=1500/max(height,width)
                new_width,new_height=int(width*scale_factor),int(height*scale_factor)
                gray=cv2.resize(gray,(new_width,new_height),interpolation=cv2.INTER_CUBIC)
                logger.info(f"Upscaled image from {width}x{height} to {new_width}x{new_height}")
            gray=_deskew_image(gray)
            gray=cv2.fastNlMeansDenoising(gray,h=10)
            clahe=cv2.createCLAHE(clipLimit=3.0,tileGridSize=(8,8))
            gray=clahe.apply(gray)
            gray=cv2.bilateralFilter(gray,9,75,75)
            _,binary=cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
            kernel=cv2.getStructuringElement(cv2.MORPH_RECT,(1,1))
            binary=cv2.morphologyEx(binary,cv2.MORPH_CLOSE,kernel)
            if np.mean(binary)<127:
                binary=cv2.bitwise_not(binary)
                logger.info("Inverted image (dark background detected)")
            result=Image.fromarray(binary)
            logger.info("Aggressive OCR preprocessing complete")
        else:
            binary=cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)
            denoised=cv2.fastNlMeansDenoising(binary)
            result=Image.fromarray(denoised)
            logger.info("Standard OCR preprocessing complete")
        return result
    except Exception as e:
        logger.warning(f"OCR preprocessing failed, using enhanced image: {e}")
        return enhance_image(image)
def _deskew_image(image:np.ndarray)->np.ndarray:
    import cv2
    try:
        coords=np.column_stack(np.where(image>0))
        if len(coords)<10:
            logger.warning("Not enough edge points for deskewing")
            return image
        angle=cv2.minAreaRect(coords)[-1]
        if angle<-45:angle=90+angle
        elif angle>45:angle=angle-90
        if abs(angle)<0.5:
            logger.info(f"Skew angle {angle:.2f}° is negligible, skipping correction")
            return image
        (h,w)=image.shape
        center=(w//2,h//2)
        M=cv2.getRotationMatrix2D(center,angle,1.0)
        rotated=cv2.warpAffine(image,M,(w,h),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
        logger.info(f"Deskewed image by {angle:.2f} degrees")
        return rotated
    except Exception as e:
        logger.warning(f"Deskew failed: {e}")
        return image
def resize_if_needed(image:Image.Image,max_size:int=2048)->Image.Image:
    width,height=image.size
    if max(width,height)>max_size:
        ratio=max_size/max(width,height)
        new_size=(int(width*ratio),int(height*ratio))
        resized=image.resize(new_size,Image.Resampling.LANCZOS)
        logger.info(f"Resized image from {image.size} to {new_size}")
        return resized
    return image
