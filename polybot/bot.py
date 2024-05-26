import telebot
from loguru import logger
import os
import time
from telebot.types import InputFile
from polybot.img_proc import Img


class Bot:

    def __init__(self, token, telegram_chat_url):
        # create a new instance of the TeleBot class.
        # all communication with Telegram servers are done using self.telegram_bot_client
        self.telegram_bot_client = telebot.TeleBot(token)

        # remove any existing webhooks configured in Telegram servers
        self.telegram_bot_client.remove_webhook()
        time.sleep(0.5)

        # set the webhook URL
        self.telegram_bot_client.set_webhook(url=f'{telegram_chat_url}/{token}/', timeout=60)

        logger.info(f'Telegram Bot information\n\n{self.telegram_bot_client.get_me()}')

    def send_text(self, chat_id, text):
        self.telegram_bot_client.send_message(chat_id, text)

    def send_text_with_quote(self, chat_id, text, quoted_msg_id):
        self.telegram_bot_client.send_message(chat_id, text, reply_to_message_id=quoted_msg_id)

    def is_current_msg_photo(self, msg):
        return 'photo' in msg

    def download_user_photo(self, msg):
        """
        Downloads the photos that sent to the Bot to `photos` directory (should be existed)
        :return:
        """
        if not self.is_current_msg_photo(msg):
            raise RuntimeError(f'Message content of type \'photo\' expected')

        file_info = self.telegram_bot_client.get_file(msg['photo'][-1]['file_id'])
        data = self.telegram_bot_client.download_file(file_info.file_path)
        folder_name = file_info.file_path.split('/')[0]

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        with open(file_info.file_path, 'wb') as photo:
            photo.write(data)

        return file_info.file_path

    def send_photo(self, chat_id, img_path):
        if not os.path.exists(img_path):
            raise RuntimeError("Image path doesn't exist")

        self.telegram_bot_client.send_photo(
            chat_id,
            InputFile(img_path)
        )

    def handle_message(self, msg):
        """Bot Main message handler"""
        logger.info(f'Incoming message: {msg}')
        self.send_text(msg['chat']['id'], f'Your original message: {msg["text"]}')


class QuoteBot(Bot):
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')

        if msg["text"] != 'Please don\'t quote me':
            self.send_text_with_quote(msg['chat']['id'], msg["text"], quoted_msg_id=msg["message_id"])


class ImageProcessingBot(Bot):
    def __init__(self, access_token, chat_endpoint):
        super().__init__(access_token, chat_endpoint)
        # Store user states for concatenation
        self.concat_state = {}

    def handle_message(self, message):
        logger.info(f'Incoming message: {message}')
        try:
            # Check if the message contains a photo
            if not self.is_current_msg_photo(message):
                self.send_text(message['chat']['id'], 'Please upload a photo with a caption for processing.')
                return

            # Download the user's photo
            img_path = self.download_user_photo(message)

            # Check if the user is in the process of concatenating images
            user_id = message['from']['id']
            if user_id in self.concat_state:
                original_img_path = self.concat_state.pop(user_id)
                self.process_concat_images(user_id, original_img_path, img_path)
                return

            # Create an Img instance for the downloaded photo
            img = Img(img_path)

            # Process the image based on the caption
            caption = message.get('caption', '').lower()
            if caption == 'blur':
                img.blur()
            elif caption == 'contour':
                img.contour()
            elif caption == 'rotate':
                img.rotate()
            elif caption == 'segment':
                img.segment()
            elif caption == 'salt and pepper':
                img.salt_n_pepper()
            elif caption == 'concat':
                self.send_text(message['chat']['id'], 'Please send the second image to concatenate with the first one.')
                self.concat_state[user_id] = img_path
                return
            else:
                self.send_text(message['chat']['id'], 'Sorry, the requested operation is not supported. Please try again with a different caption.')
                return

            # Save the processed image
            processed_img_path = img.save_img()

            # Send the processed image back to the user
            self.send_photo(message['chat']['id'], processed_img_path)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.send_text(message['chat']['id'], "Oops! Something went wrong. Please try again later.")

    def process_concat_images(self, user_id, original_img_path, second_img_path):
        try:
            original_img = Img(original_img_path)
            second_img = Img(second_img_path)
            original_img.concat(second_img)

            # Save the concatenated image
            concatenated_img_path = original_img.save_img()

            # Send the concatenated image back to the user
            self.send_photo(user_id, concatenated_img_path)

        except Exception as e:
            logger.error(f"Error concatenating images: {e}")
            self.send_text(user_id, "Oops! Something went wrong while concatenating images. Please try again later.")


