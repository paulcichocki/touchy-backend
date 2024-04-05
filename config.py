# config.py
import os

class Config:
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024
    PREFIX_URL = '/touchy-api'

    ###### Message type ######
    TEXT_Q = 100
    TEXT_A = 200
    IMAGE_Q = 101
    IMAGE_A = 201
    SELFIE_Q = 102
    SELFIE_A = 202
    SEARCH_Q = 103
    SEARCH_A = 203
