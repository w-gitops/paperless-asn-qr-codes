# pylint: disable=global-statement,global-variable-undefined,global-variable-not-assigned,used-before-assignment
""" Main module for the paperless ASN QR code generator, fills the labels with content """
import argparse
import re

from reportlab.lib.units import mm
from reportlab_qrcode import QRCodeImage

from paperless_asn_qr_codes import avery_labels

def calculate_filename(jd_prefix, start_asn, count, digits, system, prefix):
    """Calculate the default filename based on JD prefix and ASN range"""
    # Remove trailing period if present for filename
    jd = jd_prefix.rstrip('.')
    # Calculate the last ASN
    end_asn = start_asn + count - 1
    # Format both numbers with leading zeros based on digits
    start_str = f"{start_asn:0{digits}d}"
    end_str = f"{end_asn:0{digits}d}"
    return f"qr_labels_{prefix}.{system}.{jd}.{start_str} - {prefix}.{system}.{jd}.{end_str}.pdf"

def render(c, width, height, *args):
    """ Render the QR code and ASN number on the label """
    global startASN
    global digits
    global jd_prefix
    global jd_system
    global prefix
    value = f"{startASN:0{digits}d}"
    barcode_value = f"{prefix}.{jd_system}.{jd_prefix}.{value}"
    startASN = startASN + 1

    # Add small margins to ensure content isn't at the edge
    margin = .5 * mm
    
    # QR code size and position
    qr_size = height * 0.9
    qr = QRCodeImage(barcode_value, size=qr_size)
    qr.drawOn(c, margin, height * 0.05)  # Consistent left margin

    # Prefix identifier in upper right corner
    c.setFont("Helvetica", 2.5 * mm)
    prefix_width = c.stringWidth(prefix, "Helvetica", 2.5 * mm)
    # Adjust x position based on text width, keep margin from right edge
    c.drawString(width - prefix_width - 1 * mm, height - 4 * mm, prefix)

    text = c.beginText()
    # Position text to the right of QR code
    x = qr_size + .4 * margin  # More consistent spacing
    y0 = (height - 2 * mm) / 2 + 3.5 * mm

    # First line
    text.setTextOrigin(x, y0)
    text.setFont("Helvetica", 2.5 * mm)
    text.textLine(f"{prefix} ")

    # Second line
    text.setFont("Helvetica", 3 * mm)
    text.setTextOrigin(x, y0 - 3 * mm)
    
    # Save the current state
    c.saveState()
    
    # Get text dimensions for the system character
    system_width = c.stringWidth(jd_system, "Helvetica", 3 * mm)
    system_height = 3 * mm
    
    # Draw black rectangle for background
    c.setFillColor('black')
    c.rect(x, y0 - 3.25 * mm, system_width + 2 * mm, system_height + 2 * mm, fill=1)
    
    # Draw white text
    c.setFillColor('white')
    c.setFont("Helvetica", 5 * mm)
    c.drawString(x + 0.25 * mm, y0 - 2.55 * mm, jd_system)
    
    # Restore state for remaining text
    c.restoreState()
    
    # Continue with regular text
    text = c.beginText()
    text.setTextOrigin(x + system_width + 2.25 * mm, y0 - 3 * mm)
    text.setFont("Helvetica-Bold", 3 * mm)
    text.textLine(f".{jd_prefix}")

    # Third line
    text.setFont("Helvetica", 4 * mm)
    text.setTextOrigin(x - .5 *mm, y0 - 7 * mm)
    text.textLine(value)

    c.drawText(text)

def main():
    """ Main function for the paperless ASN QR code generator """
    # Match the starting position parameter. Allow x:y or n
    def _start_position(arg):
        if mat := re.match(r"^(\d{1,2}):(\d{1,2})$", arg):
            return (int(mat.group(1)), int(mat.group(2)))
        if mat := re.match(r"^\d+$", arg):
            return int(arg)
        raise argparse.ArgumentTypeError("invalid value")

    # prepare a sorted list of all formats
    available_formats = list(avery_labels.labelInfo.keys())
    available_formats.sort()

    parser = argparse.ArgumentParser(
        prog="paperless-asn-qr-codes",
        description="CLI Tool for generating paperless ASN labels with QR codes",
    )
    parser.add_argument("start_asn", type=int, help="The value of the first ASN")
    parser.add_argument(
        "output_file",
        type=str,
        nargs='?',  # Make the argument optional
        help="The output file to write to (default: auto-generated based on ASN range)",
    )
    parser.add_argument(
        "--format", "-f", choices=available_formats, default="spartan100f", help="The format of the label to use (default: spartan100f)",
    )
    parser.add_argument(
        "--digits",
        "-d",
        default=4,
        help="Number of digits in the ASN (default: 4, produces 'ASN13.08.0001')",
        type=int,
    )
    parser.add_argument(
        "--border",
        "-b",
        action="store_true",
        help="Display borders around labels, useful for debugging the printer alignment",
    )
    parser.add_argument(
        "--row-wise",
        "-r",
        action="store_true",
        help="Increment the ASNs row-wise, go from left to right. Default is row-wise.",
    )
    parser.add_argument(
        "--num-labels",
        "-n",
        type=int,
        help="Number of labels to be printed on the sheet",
    )
    parser.add_argument(
        "--pages",
        "-p",
        type=int,
        default=1,
        help="Number of pages to be printed, ignored if NUM_LABELS is set (default: 1)",
    )
    parser.add_argument(
        "--start-position",
        "-s",
        type=_start_position,
        help="""Define the starting position on the sheet,
                eighter as ROW:COLUMN or COUNT, both starting from 1 (default: 1:1 or 1)""",
    )
    parser.add_argument(
        "--jd", 
        "-jd",
        type=str,
        default="13.08",
        help="""Johnny Decimal prefix (default: 13.08)""",
    )
    parser.add_argument(
        "--jd-system",
        "-js",
        type=str,
        default="P",
        help="Johnny Decimal system identifier (single character, default: P)",
        metavar="CHAR"
    )
    parser.add_argument(
        "--prefix",
        "-pre",
        type=str,
        default="ASN",
        help="Prefix for the label and barcode (default: ASN)",
    )

    args = parser.parse_args()
    
    # Validate jd_system is a single character
    if len(args.jd_system) != 1:
        parser.error("--jd-system must be a single character")

    global startASN
    global digits
    global jd_system
    global prefix
    startASN = int(args.start_asn)
    digits = int(args.digits)
    jd_system = args.jd_system
    prefix = args.prefix

    # Ensure trailing period
    global jd_prefix
    jd_prefix = args.jd

    # Create the label object FIRST
    label = avery_labels.AveryLabel(
        args.format, args.border, topDown=args.row_wise, start_pos=args.start_position
    )

    # THEN calculate count
    if args.num_labels:
        count = args.num_labels
    else:
        # Otherwise number of pages*labels - offset
        count = args.pages * label.across * label.down - label.position
    count = int(count)

    # Generate default filename if none provided
    output_file = args.output_file
    if output_file is None:
        output_file = calculate_filename(jd_prefix, startASN, count, digits, jd_system, prefix)

    # Open the file and render
    label.open(output_file)
    label.render(render, count)
    label.close()
