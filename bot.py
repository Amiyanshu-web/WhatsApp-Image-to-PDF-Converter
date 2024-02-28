from pyngrok import ngrok
from flask import Flask, request, jsonify, make_response

import io
import requests
from requests.auth import HTTPBasicAuth
from PIL import Image
from reportlab.pdfgen import canvas

from twilio.rest import Client

twilio_sid = "your sid"
twilio_key = "your key"

body = []
link = []
pdf = None
file_name = None

ngrok.set_auth_token('your auth token')
port = 5000
public_url = ngrok.connect(port).public_url

app = Flask(__name__)

def send_message(sender, raw_url):
  client = Client(twilio_sid, twilio_key)

  msg = f"""
Click on the link to download your pdf file:
{raw_url}

After downloading, reply with 'OK' to delete the file from repository.
        """

  message = client.messages \
      .create(
          body=msg,
          from_='whatsapp: your  whatsApp number',
          to=sender

      )
      
      
def get_image(x):    
  res = requests.get(x, auth=HTTPBasicAuth(twilio_sid, twilio_key))
  image_data = res.content
  image_stream = io.BytesIO(image_data)
  image = Image.open(image_stream)
  return image

def to_pdf(body, link, sender):
  global pdf
  tmp = body.copy()
  tmp.sort()

  # Create a BytesIO object to hold the PDF
  pdf_bytes = io.BytesIO()
  # Create a new PDF with Reportlab
  c = canvas.Canvas(pdf_bytes)

  if len(body) > 1:
    for i in tmp:
      image = get_image(link[body.index(i)])
      c.setPageSize(image.size)
      c.drawInlineImage(image, 0, 0)
      c.showPage()

  else:
    for i in link:
      image = get_image(i)
      c.setPageSize(image.size)
      c.drawInlineImage(image, 0, 0)
      c.showPage()

  c.save()

  send_message(sender, public_url+"/download_pdf")
  
  pdf =  bytes(pdf_bytes.getvalue())
  

#1
@app.route("/", methods=["GET"])
def handle_request():
  return f'Up and running...<br><br> Copy this link for the twilio endpoint:<br><u>{public_url}/listening-from-twilio</u>'

#2
@app.route('/listening-from-twilio', methods=['POST'])
def reply():
  global pdf
  global file_name
  global body
  global link

  sender = request.form.get('From')
  message = request.form.get('Body')
  media_url = request.form.get('MediaUrl0')

  if message.lower() == 'convert':
    to_pdf(body, link, sender)

  elif message.lower() == 'ok':
    pdf = None
    file_name = None
    ## ADD CODE TO DELETE IMAGES FROM TWILIO CDN
    body = []
    link = []

  elif 'name:' in message.lower():
    file_name = message.lower().split('name:')[1].strip().upper()

  else:
    if (message != '') and (len(body) == len(link)):
      body.append(int(message))
    else:
      pass
    link.append(media_url)

  return '200'

#3
@app.route("/download_pdf", methods=['GET'])
def download_pdf():
  global pdf
  global file_name
  if not pdf:
    return "PDF file does not exist.. sorry for the inconvenience"
  else:
    response = make_response(pdf, 200)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={file_name if file_name != None else "converted"}.pdf'
    return response

print(public_url)
print(public_url + '/listening-from-twilio')
app.run(port=port)
      