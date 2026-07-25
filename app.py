import logging
import os

import cv2
import numpy as np
from dotenv import load_dotenv
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename

# ---------------------------------------------------
# Load Environment Variables
# ---------------------------------------------------
load_dotenv()

# ---------------------------------------------------
# Logging Configuration
# ---------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------
# Configuration
# ---------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.getenv(
    "UPLOAD_FOLDER",
    os.path.join(BASE_DIR, "static", "uploads")
)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

PORT = int(os.getenv("PORT", 4000))

DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"

SECRET_KEY = os.getenv("SECRET_KEY", "change-me")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------------------------------------------
# Flask App
# ---------------------------------------------------

app = Flask(__name__)

app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SECRET_KEY"] = SECRET_KEY


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------------------------------------------
# Sketch Generator
# ---------------------------------------------------

def make_sketch(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    smooth = cv2.bilateralFilter(gray, 9, 90, 90)
    edges = cv2.Laplacian(smooth, cv2.CV_8U, ksize=5)
    edges = cv2.bitwise_not(edges)
    inv = cv2.bitwise_not(smooth)
    blur = cv2.GaussianBlur(inv, (27, 27), 0)
    shading = cv2.divide(smooth, 255 - blur, scale=250)
    final = cv2.multiply(shading, edges, scale=1 / 255)

    final = cv2.normalize(final, None, 0, 255, cv2.NORM_MINMAX)
    final = final.astype(np.uint8)

    return final


# ---------------------------------------------------
# Cartoon Generator
# ---------------------------------------------------

def make_cartoon(img):
    color = cv2.bilateralFilter(img, d=9, sigmaColor=200, sigmaSpace=200)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray_blur = cv2.medianBlur(gray, 7)

    edges = cv2.adaptiveThreshold(
        gray_blur,
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        blockSize=9,
        C=2,
    )

    edges_3c = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    cartoon = cv2.bitwise_and(color, edges_3c)

    return cartoon


# ---------------------------------------------------
# Routes
# ---------------------------------------------------

@app.route("/", methods=["GET"])
def home():
    return render_template("home.html")


@app.route("/sketch", methods=["POST"])
def sketch():

    if "file" not in request.files:
        logger.warning("No file part in request")
        return "No file part", 400

    file = request.files["file"]

    if file.filename == "":
        logger.warning("No file selected")
        return "No file selected", 400

    if file and allowed_file(file.filename):

        try:

            filename = secure_filename(file.filename)

            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

            file.save(file_path)

            img = cv2.imread(file_path)

            if img is None:
                logger.error("Unable to read uploaded image")
                return "Image read error", 400

            sketch_img = make_sketch(img)

            sketch_img_name = f"{os.path.splitext(filename)[0]}_sketch.jpg"

            cv2.imwrite(
                os.path.join(app.config["UPLOAD_FOLDER"], sketch_img_name),
                sketch_img,
            )

            cartoon_img = make_cartoon(img)

            cartoon_img_name = f"{os.path.splitext(filename)[0]}_cartoon.jpg"

            cv2.imwrite(
                os.path.join(app.config["UPLOAD_FOLDER"], cartoon_img_name),
                cartoon_img,
            )

            logger.info(f"Successfully processed {filename}")

            return render_template(
                "home.html",
                org_img_name=filename,
                sketch_img_name=sketch_img_name,
                cartoon_img_name=cartoon_img_name,
            )

        except Exception as e:
            logger.exception(f"Error processing image: {e}")
            return "Internal Server Error", 500

    logger.warning("Invalid file type uploaded")
    return "Invalid file type", 400


@app.route("/health", methods=["GET"])
def health():

    return {
        "status": "UP",
        "application": "Image-to-Sketch",
        "version": "1.0",
    }, 200


# ---------------------------------------------------
# Run Application
# ---------------------------------------------------

if __name__ == "__main__":

    logger.info(f"Application started on port {PORT}")

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=DEBUG,
    )