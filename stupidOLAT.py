#!/usr/bin/env python3
import argparse
import re
import markdown
from bs4 import BeautifulSoup
import os
import sys
import glob

import json
import base64
from io import BytesIO
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import GappedSquareModuleDrawer
from qrcode.image.styles.colormasks import RadialGradiantColorMask

def convert_markdown_to_html(markdown_text):
    """Convert markdown text to HTML."""
    ## Configure markdown
    config = {
        'extra': {
            'footnotes': {
                'UNIQUE_IDS': True,
            },
            'fenced_code': {
                'lang_prefix': 'lang-'
            }
        },
        'toc': {
            'permalink': True
        }
    }

    ## Convert Markdown to HTML using Python-Markdown
    html = markdown.markdown(markdown_text, extensions=['extra', 'sane_lists', 'smarty', 'toc'], extension_configs=config)
    return html

def replace_headers(html_content):
    """Replace h1-h6 tags with the specific styling used in the LMS while preserving IDs and anchor links."""
    # Create a BeautifulSoup object to parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Define styles for different header levels
    header_styles = {
        'h1': '<span style="font-family: \'arial black\', \'avant garde\'; color: #5fac22; font-size: 36pt;"><strong>{}</strong></span>',
        'h2': '<span style="font-family: \'arial black\', \'avant garde\'; color: #5fac22; font-size: 36pt;"><strong>{}</strong></span>',
        'h3': '<span style="color: #7e8c8d; font-family: \'arial black\', \'avant garde\';"><strong>{}</strong></span>',
        'h4': '<span style="color: #7e8c8d; font-family: \'arial black\', \'avant garde\';"><strong>{}</strong></span>',
        'h5': '<span style="color: #7e8c8d; font-family: \'arial black\', \'avant garde\';"><strong>{}</strong></span>',
        'h6': '<span style="color: #7e8c8d; font-family: \'arial black\', \'avant garde\';"><strong>{}</strong></span>'
    }
    
    # Find all header tags and modify them to include the styled spans
    for tag_name, style_template in header_styles.items():
        for tag in soup.find_all(tag_name):
            # Extract the text content, preserving only the text
            header_text = ""
            anchor_link = ""
            for content in tag.contents:
                if isinstance(content, str):
                    header_text += content
                elif content.name != 'a' and content.string:  # Skip anchor links but include other content
                    header_text += content.string
                elif content.name == 'a':
                    anchor_link = content
            
            # Apply style to header text.
            header_text = BeautifulSoup(style_template.format(header_text), 'html.parser')
            
            # Preserve the original ID and any attributes
            tag_attrs = tag.attrs.copy()
            
            # Clear the content but keep the original tag
            tag.clear()
            
            # Restore the original attributes
            for attr_name, attr_value in tag_attrs.items():
                tag[attr_name] = attr_value
            
            tag.append(header_text)
            tag.append(anchor_link)
    
    return str(soup)

def handle_code_blocks(html_content):
    """Format code blocks with appropriate styling."""
    # Create a BeautifulSoup object to parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all code blocks (pre tags)
    for pre in soup.find_all('pre'):
        # Create a new div with the code styling
        code_div = soup.new_tag('div', attrs={'class': 'b_code'})
        code_div.append(pre)
        pre.wrap(code_div)
    
    return str(soup)

def handle_blockquotes(html_content):
    """Format blockquotes with the LMS style based on task type."""
    # Create a BeautifulSoup object to parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all blockquote tags
    for blockquote in soup.find_all('blockquote'):
        # Determine the task type based on the first line or special marker
        # b_note b_info b_important b_success b_warning b_error b_tip
        task_type = 'b_info'  # Default for mandatory preparation tasks

        # Check if the blockquote has a special marker
        first_line = None
        for content in blockquote.contents:
            if content.name == 'p':
                first_line = content.get_text().strip()
                break

        # Check for task type markers in the first line
        if first_line:
            if first_line.startswith('[class]') or first_line.startswith('[in-class]'):
                task_type = 'b_warning'
                # Remove the marker from the first line
                if content.name == 'p':
                    content.string = content.get_text().replace('[class]', '').replace('[in-class]', '').strip()
                    if not content.string:  # If the paragraph is now empty
                        content.extract()  # Remove the empty paragraph
            elif first_line.startswith('[post]') or first_line.startswith('[after-class]'):
                task_type = 'b_success'
                # Remove the marker from the first line
                if content.name == 'p':
                    content.string = content.get_text().replace('[post]', '').replace('[after-class]', '').strip()
                    if not content.string:  # If the paragraph is now empty
                        content.extract()  # Remove the empty paragraph
            elif first_line.startswith('[pre]') or first_line.startswith('[before-class]'):
                task_type = 'b_important'
                # Remove the marker from the first line
                if content.name == 'p':
                    content.string = content.get_text().replace('[pre]', '').replace('[before-class]', '').strip()
                    if not content.string:  # If the paragraph is now empty
                        content.extract()  # Remove the empty paragraph
        
        # Create a new div with the appropriate styling
        styled_div = soup.new_tag('div', attrs={'class': task_type})

        # Move the content from blockquote to the new div
        for content in blockquote.contents:
            ## The extract() gets content and deletes it in origin node.
            styled_div.append(content.extract())
        
        # print(styled_div)
        # Replace the original blockquote with our new div
        blockquote.replace_with(styled_div)
    
    return str(soup)

def handle_images(html_content):
    """Format images with the LMS style."""
    # Create a BeautifulSoup object to parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all img tags
    for img in soup.find_all('img'):
        # Create figure and figcaption tags for proper image formatting
        figure = soup.new_tag('figure', attrs={'class': 'image align-center'})
        img['class'] = 'b_centered'
        
        # Set a default width if not specified
        if not img.get('width'):
            img['width'] = '80%'
        
        # Check if there's a caption (in a paragraph immediately following)
        next_sibling = img.find_next_sibling()
        if next_sibling and next_sibling.name == 'p' and next_sibling.get_text().strip().startswith('Caption:'):
            caption = next_sibling.extract()
            figcaption = soup.new_tag('figcaption')
            figcaption.string = caption.get_text().replace('Caption:', '').strip()
            
            # Replace the img tag with the figure structure
            img.replace_with(figure)
            figure.append(img)
            figure.append(figcaption)
        else:
            # No caption found, just wrap the image in a figure
            img.replace_with(figure)
            figure.append(img)
    
    return str(soup)

def handle_tables(html_content):
    """Format tables with the LMS style."""
    # Create a BeautifulSoup object to parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all table tags
    for table in soup.find_all('table'):
        # Add the default class to the table
        table['class'] = 'b_default'
        table['style'] = 'border-collapse: collapse; width: 100%;'
    
    return str(soup)

def add_lms_structure(html_content, title):
    """Add the LMS document structure and styling."""
    # Format the title as h2 with the specific styling
    # formatted_title = f'<h2><span style="font-family: \'arial black\', \'avant garde\'; color: #5fac22; font-size: 36pt;"><strong>{title}</strong></span></h2>'
    
    # Assemble the full HTML content with the LMS structure
    lms_html = f'''{html_content}'''
    
    return lms_html


def handle_group_links_json(html_content):
    """Process group-specific links defined in JSON format and convert them to tables with QR codes."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all pre elements that might contain our group links JSON
    for pre in soup.find_all('pre'):
        # Check if this pre block contains our group links marker
        if pre.string and '[group_links]' in pre.string:
            try:
                # Extract the JSON data
                json_text = pre.string.split('[group_links]', 1)[1].strip()
                group_links = json.loads(json_text)
                
                if not group_links:  # Empty dictionary
                    continue
                
                # Create a table with the group names and links               
                table = soup.new_tag('table', attrs={
                    'class': 'b_default group-links-table', 
                    'style': 'border-collapse: collapse; width: 100%; margin: 3ex'
                })
                
                # Create header row with group names
                thead = soup.new_tag('thead', attrs={
                    'style': 'border-top: 2px solid #666; border-bottom: 1px solid #666;'
                })
                tr = soup.new_tag('tr')
                
                for group_name in group_links.keys():
                    th = soup.new_tag('th', attrs={'style': 'text-align: center;'})
                    strong = soup.new_tag('strong')
                    strong.string = group_name
                    th.append(strong)
                    tr.append(th)
                
                thead.append(tr)
                table.append(thead)
                
                # Create table body
                tbody = soup.new_tag('tbody', attrs={
                    'style': 'border-bottom: 2px solid #666;'
                })
                # Create row with QR codes
                qr_tr = soup.new_tag('tr')
                
                for group_name, link in group_links.items():
                    # Generate QR code
                    qr = qrcode.QRCode(
                        version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,
                        border=1
                    )
                    qr.add_data(link)
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="black", back_color="white", image_factory=StyledPilImage, module_drawer=GappedSquareModuleDrawer())
                    
                    # Convert the QR code image to a base64 string for embedding in HTML
                    buffered = BytesIO()
                    img.save(buffered, format="PNG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    
                    # Create a cell with the QR code
                    td = soup.new_tag('td', attrs={'style': 'text-align: center;'})
                    img_tag = soup.new_tag('img', attrs={
                        'src': f"data:image/png;base64,{img_str}",
                        'alt': f"QR Code for {group_name}",
                        'style': 'display: inline; position: relative; width: 50%; height: 50%;'
                    })
                    td.append(img_tag)
                    qr_tr.append(td)
                
                tbody.append(qr_tr)
                
                # Create row with links
                link_tr = soup.new_tag('tr')
                
                for group_name, link in group_links.items():
                    td = soup.new_tag('td', attrs={'style': 'text-align: center;'})
                    a = soup.new_tag('a', attrs={'href': link, 'target': '_blank', 'rel': 'noopener'})
                    a.string = "Link öffnen"
                    td.append(a)
                    link_tr.append(td)
                
                tbody.append(link_tr)
                table.append(tbody)
                
                # Replace the original pre block with the table
                pre.replace_with(table)
                
            except json.JSONDecodeError as e:
                # If there's an error parsing the JSON, add an error message
                error_div = soup.new_tag('div', attrs={'class': 'b_error'})
                error_div.string = f"Error parsing group links JSON: {str(e)}"
                pre.replace_with(error_div)
            except ImportError:
                # If qrcode module is not installed
                error_div = soup.new_tag('div', attrs={'class': 'b_error'})
                error_div.string = "Error: The 'qrcode' module is not installed. Run 'pip install qrcode Pillow' to install it."
                pre.replace_with(error_div)
    
    return str(soup)

def process_file(input_file, output_file=None, title=None):
    """Process a markdown file and convert it to LMS HTML format."""
    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        markdown_text = f.read()
    
    # Extract title from first line if not provided
    if not title:
        first_line = markdown_text.split('\n', 1)[0].strip('# ')
        title = first_line
        # Remove the first line from the markdown text if it's a title
        if markdown_text.startswith('# '):
            markdown_text = markdown_text.split('\n', 1)[1]
    
    # Convert markdown to HTML
    html_content = convert_markdown_to_html(markdown_text)
    
    # Apply transformations
    html_content = replace_headers(html_content)
    html_content = handle_blockquotes(html_content)
    html_content = handle_images(html_content)
    html_content = handle_tables(html_content)
    html_content = handle_group_links_json(html_content)  # Added the new function
    html_content = handle_code_blocks(html_content)

    
    # Add LMS structure
    lms_html = add_lms_structure(html_content, title)
    
    # Determine output file name if not provided
    if not output_file:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}.html"
    
    # Write the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(lms_html)
    
    print(f"Converted {input_file} to {output_file}")
    return output_file

def process_folder(input_folder, output_folder, title=None):
    """Process all markdown files in a folder and convert them to LMS HTML format."""
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output folder: {output_folder}")
    
    # Find all markdown files in the input folder
    md_file_pattern = os.path.join(input_folder, "*.md")
    md_files = glob.glob(md_file_pattern)
    
    if not md_files:
        print(f"No markdown files found in {input_folder}")
        return
    
    files_processed = 0
    for md_file in md_files:
        # Determine the output file path
        base_name = os.path.basename(md_file)
        output_file = os.path.join(output_folder, os.path.splitext(base_name)[0] + '.html')
        
        #try:
        process_file(md_file, output_file, title)
        files_processed += 1
        #except Exception as e:
        #    print(f"Error processing {md_file}: {str(e)}")
    
    print(f"\nProcess complete. Converted {files_processed} out of {len(md_files)} files.")

def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description='Convert Markdown to LMS-compatible HTML')
    
    # Create a mutually exclusive group for file vs folder mode
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--file', help='Process a single markdown file')
    group.add_argument('-i', '--input-folder', help='Input folder containing markdown files to convert')
    
    # Other arguments
    parser.add_argument('-o', '--output', help='The output file (for single file mode) or folder (for folder mode)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Process based on mode
    if args.file:
        # Single file mode
        output_file = args.output
        process_file(args.file, output_file)
    else:
        # Folder mode
        input_folder = args.input_folder
        output_folder = args.output or os.path.join(os.path.dirname(input_folder), "html_output")
        process_folder(input_folder, output_folder)

if __name__ == "__main__":
    main()
