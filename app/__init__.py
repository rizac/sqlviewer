from flask import Flask

app = Flask(__name__)

from app import views  # @NoMove # pylint:disable=E402 @IgnorePep8
