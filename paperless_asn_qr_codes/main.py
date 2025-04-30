# pylint: disable=global-statement,global-variable-undefined,global-variable-not-assigned,used-before-assignment
""" Main module for the paperless ASN QR code generator, fills the labels with content """
import argparse
import re

from reportlab.lib.units import mm
from reportlab_qrcode import QRCodeImage

from paperless_asn_qr_codes import avery_labels

def render(c, width, height, *args):
    """ Render the QR code and ASN number on the label """
    global startASN
    global digits
    global jd_prefix
    value = f"{startASN:0{digits}d}"  # Just the number, no prefix
    barcode_value = f"ASN{jd_prefix}{value}"  # With JD prefix for QR code
    startASN = startASN + 1

    # Add small margins to ensure content isn't at the edge
    margin = 1 * mm
    
    # QR code size and position
    qr_size = height * 0.9
    qr = QRCodeImage(barcode_value, size=qr_size)
    qr.drawOn(c, margin, height * 0.05)  # Consistent left margin

    text = c.beginText()
    # Position text to the right of QR code
    x = qr_size + 2 * margin  # More consistent spacing
    y0 = (height - 2 * mm) / 2 + 3.5 * mm

    # First line
    text.setTextOrigin(x, y0)
    text.setFont("Helvetica", 2.5 * mm)
    text.textLine("ASN ")

    # Second line
    text.setFont("Helvetica", 3 * mm)
    text.setTextOrigin(x, y0 - 3 * mm)
    text.textLine(f"{jd_prefix}")

    # Third line
    text.setFont("Helvetica", 4 * mm)
    text.setTextOrigin(x, y0 - 7 * mm)
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
        default="labels.pdf",
        help="The output file to write to (default: labels.pdf)",
    )
    parser.add_argument(
        "--format", "-f", choices=available_formats, default="averyL4731"
    )
    parser.add_argument(
        "--digits",
        "-d",
        default=4,
        help="Number of digits in the ASN (default: 4, produces 'ASN000001')",
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
        action="store_false",
        help="Increment the ASNs row-wise, go from left to right",
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

    args = parser.parse_args()
    global startASN
    global digits
    startASN = int(args.start_asn)
    digits = int(args.digits)

    # Ensure trailing period
    global jd_prefix
    jd_prefix = args.jd if args.jd.endswith('.') else args.jd + '.'


    label = avery_labels.AveryLabel(
        args.format, args.border, topDown=args.row_wise, start_pos=args.start_position
    )
    label.open(args.output_file)

    # If defined use parameter for number of labels
    if args.num_labels:
        count = args.num_labels
    else:
        # Otherwise number of pages*labels - offset
        count = args.pages * label.across * label.down - label.position
    count = int(count)  # Convert to integer

    # Call render with just the function and count
    label.render(render, count)
    label.close()
