# Welcome Video Setup Guide

## Overview
The applicant portal now features a professional welcome video section that displays before job listings. This provides candidates with a first impression of your company culture and benefits.

## Features Added

### 1. **Welcome Video Section** (`index.html`)
- **Location**: Top of applicant landing page (after header, before job listings)
- **Layout**: Two-column responsive design
  - Left: Company welcome text + 4 key benefits
  - Right: Embedded video player
- **Styling**: 
  - Gradient background (teal to dark blue)
  - Smooth animations on page load
  - Fully responsive (stacks on mobile)

### 2. **Enhanced Search & Filter**
- Working keyword search across job titles and descriptions
- Department filtering
- Location filtering
- Real-time filtering with smooth opacity transitions

### 3. **CSS Styling**
- Animated slide-in effect (slideInDown)
- Professional color scheme matching project colors:
  - Primary: #124e66 (teal)
  - Secondary: #0a2338 (dark)
  - Accent: #f39c12 (orange)
- Mobile-responsive (768px breakpoint)

---

## How to Customize the Video

### Option 1: Use an Embedded Video URL (Recommended)
1. Host your company welcome video on a video platform:
   - YouTube (unlisted or public)
   - Vimeo
   - AWS S3
   - Your own server
   - Any CORS-enabled video hosting service

2. Edit `templates/index.html` (line ~453):
   ```html
   <video controls poster="">
       <source src="YOUR_VIDEO_URL_HERE" type="video/mp4">
   ```

   Replace `YOUR_VIDEO_URL_HERE` with your actual video URL.

   **Example:**
   ```html
   <!-- YouTube (embed URL format) -->
   <source src="https://www.youtube.com/embed/YOUR_VIDEO_ID" type="video/mp4">
   
   <!-- Direct MP4 -->
   <source src="https://my-bucket.s3.amazonaws.com/welcome-video.mp4" type="video/mp4">
   
   <!-- Local file in static folder -->
   <source src="{{ url_for('static', filename='videos/welcome.mp4') }}" type="video/mp4">
   ```

### Option 2: Replace the Video Player Component
If you want a different video player (e.g., custom player, YouTube embed, etc.):

Replace the entire video section in `templates/index.html` (lines 450-460):
```html
<!-- Example: YouTube Embed -->
<div class="welcome-video">
    <iframe width="100%" height="100%" 
        src="https://www.youtube.com/embed/YOUR_VIDEO_ID" 
        title="Company Welcome Video"
        frameborder="0" 
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
        allowfullscreen>
    </iframe>
</div>
```

### Option 3: Add a Video to Static Folder
1. Create folder: `static/videos/`
2. Add your video file: `static/videos/welcome.mp4`
3. Update source tag:
   ```html
   <source src="{{ url_for('static', filename='videos/welcome.mp4') }}" type="video/mp4">
   ```

---

## Video Specifications

### Recommended Format
- **Container**: MP4 (H.264 video codec)
- **Resolution**: 1920x1080 (16:9 aspect ratio)
- **Duration**: 30-120 seconds recommended
- **File Size**: 50-200 MB (smaller is better for loading)
- **Bitrate**: 2000-5000 kbps

### Video Compression
To optimize for web, use FFmpeg:
```bash
ffmpeg -i input-video.mp4 \
  -vcodec h264 \
  -b:v 2500k \
  -acodec aac \
  -b:a 128k \
  -s 1920x1080 \
  output-video.mp4
```

---

## Content Suggestions

Your 60-second welcome video should include:

1. **Opening (5-10 sec)**
   - Company logo or team shot
   - "Welcome to [Company Name]"

2. **Culture & Values (20-30 sec)**
   - Office/workspace tour
   - Team members speaking (testimonials)
   - Company culture highlights

3. **Key Benefits (15-25 sec)**
   - What makes your company unique
   - Career growth opportunities
   - Work environment perks

4. **Call to Action (5-10 sec)**
   - Encourage applying
   - Company tagline
   - Contact information

---

## Customizing Welcome Text & Benefits

The welcome section left column displays company information. Edit in `templates/index.html` (lines 429-447):

```html
<h2><i class="fas fa-star" style="color: #f39c12;"></i> Welcome to [YOUR COMPANY]</h2>
<p>Your company description here...</p>

<div class="welcome-benefits">
    <div class="benefit-item">
        <i class="fas fa-check-circle"></i>
        <span>Your benefit #1</span>
    </div>
    <div class="benefit-item">
        <i class="fas fa-check-circle"></i>
        <span>Your benefit #2</span>
    </div>
    <!-- Add/remove benefits as needed -->
</div>
```

---

## Styling Customization

### Colors
Edit CSS in `templates/index.html` (search `.welcome-section`):

```css
.welcome-section {
    background: linear-gradient(135deg, #124e66 0%, #0a2338 100%);
    /* Change to your preferred gradient */
}
```

### Spacing & Size
- `.welcome-content` - Container spacing (default: `padding: 50px; gap: 40px`)
- `.welcome-text h2` - Title font size (default: `32px`)
- `.welcome-video` - Video container dimensions

### Animations
- `.welcome-section` has `animation: slideInDown 0.8s ease-out`
- Modify timing in `@keyframes slideInDown` (lines ~192-200)

---

## Testing

1. **Local Testing**:
   ```bash
   python app.py
   ```
   Navigate to: `http://localhost:5000/`

2. **Video Loading**:
   - Check browser console (F12) for any CORS errors
   - Verify video URL is accessible
   - Test on different browsers (Chrome, Firefox, Safari, Edge)

3. **Responsive Testing**:
   - Desktop: Full two-column layout
   - Tablet (900px): Two columns with adjusted spacing
   - Mobile (<900px): Stacked single column

---

## Performance Tips

1. **Video Hosting**:
   - Use CDN for faster delivery (CloudFront, Cloudflare)
   - Enable video caching headers

2. **Video Compression**:
   - Keep video under 100MB
   - Use H.264 codec for broad compatibility
   - Consider multiple bitrates for adaptive streaming

3. **Fallback Content**:
   - Poster image shows before video loads
   - Text content still displays if video fails
   - Add `poster="image-url.jpg"` for custom thumbnail

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Video won't play | Check URL is accessible, CORS enabled, format is MP4 |
| Video looks blurry | Increase bitrate or use higher resolution source |
| Layout looks broken on mobile | CSS already responsive, clear browser cache |
| Video takes too long to load | Compress video file, use CDN hosting |
| Controls don't show | Add `controls` attribute to `<video>` tag |

---

## Example: Using Local Video File

1. Place video in: `static/videos/welcome.mp4`
2. Update `templates/index.html`:
```html
<video controls poster="{{ url_for('static', filename='videos/welcome-poster.jpg') }}">
    <source src="{{ url_for('static', filename='videos/welcome.mp4') }}" type="video/mp4">
    <p>Your browser doesn't support HTML5 video.</p>
</video>
```

---

## Accessibility

The video player includes:
- ✅ Native HTML5 controls
- ✅ Alternative text description
- ✅ Keyboard navigation
- ✅ Mobile-friendly touch controls

Consider adding:
- Captions/subtitles (WebVTT format)
- Audio descriptions for vision-impaired users
- Transcript of video content

---

## Next Steps

1. ✅ **Prepare your video** (30-120 seconds, MP4 format)
2. ✅ **Host the video** (URL or static folder)
3. ✅ **Update video URL** in `templates/index.html`
4. ✅ **Customize welcome text** to match your company
5. ✅ **Test on multiple devices** (desktop, tablet, mobile)
6. ✅ **Monitor analytics** - track video engagement

---

## Support

For issues or customization help:
- Check browser console for error messages (F12)
- Verify video URL is publicly accessible
- Test video on different browsers
- Clear browser cache if changes don't appear

Last Updated: 2026-06
