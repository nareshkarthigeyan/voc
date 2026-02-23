from flask import Flask, render_template, request, redirect, url_for
import xml.etree.ElementTree as ET
import os
import uuid

app = Flask(__name__)
XML_FILE = "users.xml"

# Ensure XML file exists
if not os.path.exists(XML_FILE):
    root = ET.Element("users")
    tree = ET.ElementTree(root)
    tree.write(XML_FILE)

def add_user(data):
    tree = ET.parse(XML_FILE)
    root = tree.getroot()

    user = ET.SubElement(root, "user")
    ET.SubElement(user, "name").text = data["name"]
    ET.SubElement(user, "age").text = data["age"]
    ET.SubElement(user, "department").text = data["department"]
    ET.SubElement(user, "designation").text = data["designation"]
    ET.SubElement(user, "employee_id").text = data["employee_id"]
    ET.SubElement(user, "user_id").text = str(uuid.uuid4())[:8]

    tree.write(XML_FILE)

@app.route("/")
def home():
    return redirect(url_for("register"))

@app.route("/register", methods=["GET", "POST"])
def register():
    message = ""
    if request.method == "POST":
        data = {
            "name": request.form["name"],
            "age": request.form["age"],
            "department": request.form["department"],
            "designation": request.form["designation"],
            "employee_id": request.form["employee_id"]
        }
        add_user(data)
        return render_template("register.html", message="✅ User registered successfully!")
    return render_template("register.html", message="")

if __name__ == "__main__":
    app.run(debug=True)
