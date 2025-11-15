from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import io

def generate_barcode_with_name(data, name, filename="barcode.png"):
    # Generate the barcode without text (we'll add our own)
    options = {
        'module_width': 0.3,
        'module_height': 12,
        'quiet_zone': 3,
        'font_size': 0,  # Disable default text
        'text_distance': 0,
        'background': 'white',
        'foreground': 'black',
    }
    
    code = Code128(data, writer=ImageWriter())
    
    # Save to bytes buffer
    buffer = io.BytesIO()
    code.write(buffer, options=options)
    buffer.seek(0)
    
    # Open the barcode image
    barcode_img = Image.open(buffer)
    
    # Create a new image with space for name and number
    barcode_width, barcode_height = barcode_img.size
    padding = 40
    text_height = 50  # Reduced space for name at top (was 60)
    number_height = 75  # Increased space for number at bottom (was 50)
    
    total_width = barcode_width + (padding * 2)
    total_height = barcode_height + text_height + number_height
    
    final_img = Image.new('RGB', (total_width, total_height), 'white')
    
    # Paste the barcode in the middle
    barcode_x = (total_width - barcode_width) // 2
    barcode_y = text_height
    final_img.paste(barcode_img, (barcode_x, barcode_y))
    
    # Setup drawing
    draw = ImageDraw.Draw(final_img)
    
    # Try to load fonts
    try:
        name_font = ImageFont.truetype("arial.ttf", 28)
        number_font = ImageFont.truetype("arial.ttf", 32)  # Increased from 24 to 32
    except:
        try:
            name_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 28)
            number_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 32)  # Increased from 24 to 32
        except:
            name_font = ImageFont.load_default()
            number_font = ImageFont.load_default()
    
    # Draw the name at the top (centered, closer to barcode)
    name_bbox = draw.textbbox((0, 0), name, font=name_font)
    name_width = name_bbox[2] - name_bbox[0]
    name_x = (total_width - name_width) // 2
    name_y = 15  # Moved down from 10 to 15
    draw.text((name_x, name_y), name, fill='black', font=name_font)
    
    # Draw the number at the bottom (centered)
    number_bbox = draw.textbbox((0, 0), data, font=number_font)
    number_width = number_bbox[2] - number_bbox[0]
    number_x = (total_width - number_width) // 2
    number_y = text_height + barcode_height + 10  # Increased margin for larger font
    draw.text((number_x, number_y), data, fill='black', font=number_font)
    
    # Save the final image
    final_img.save(filename)
    return final_img

# Your data as an array of tuples (number, name)
people_data = [
    ("02289428", "Aura Rachmina"),
    ("02307126", "Sudinah"),
    ("02285071", "Sukino"),
    ("02318554", "Andi Correa"),
    ("02318735", "Bambang Suparno"),
    ("01233049", "Iriana"),
    ("02299640", "Nurul Afifah Rahmasari"),
    ("02300184", "Muji Wati"),
    ("01701823", "Muhammad Fauzan"),
    ("02319359", "Triyanto"),
    ("01892880", "Marda Afifah"),
    ("02305155", "Hiwan Prasetyo"),
    ("02309342", "Karyono"),
    ("02308058", "Supriyanto"),
    ("02316251", "Setiani Prihartati"),
    ("02317316", "Sukarno"),
    ("02318300", "Rejeb"),
    ("02318654", "Meki Setiawan"),
    ("02318906", "Misngatin"),
    ("02318511", "Lasiah"),
    ("02250980", "Ir Suparno"),
    ("02301756", "Sukamti")
]

# Generate barcodes for all people
for number, name in people_data:
    # Create filename: number_name.png
    # Replace spaces with underscores and remove any problematic characters
    safe_name = name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    filename = f"{number}_{safe_name}.png"
    
    print(f"Generating barcode for {name} ({number}) -> {filename}")
    generate_barcode_with_name(number, name, filename)

print(f"Generated {len(people_data)} barcodes!")
