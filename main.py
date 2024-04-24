import cv2
import math

from kivy.uix.gridlayout import GridLayout

from object_detector import *
import numpy as np
import os
from model import TensorFlowModel

import PIL.Image
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Rectangle, Line
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.graphics.texture import Texture
from kivy.uix.camera import Camera
from kivy.network.urlrequest import UrlRequest
from kivy.graphics import PushMatrix, PopMatrix, Rotate
from kivy.uix.screenmanager import ScreenManager,Screen,SlideTransition
from kivy.uix.scrollview import ScrollView

# Initialize variables
labels = {0: 'apple', 1: 'banana', 2: 'beetroot', 3: 'bell pepper', 4: 'cabbage', 5: 'capsicum', 6: 'carrot',
          7: 'cauliflower', 8: 'chilli pepper', 9: 'corn', 10: 'cucumber', 11: 'eggplant', 12: 'garlic', 13: 'ginger',
          14: 'grapes', 15: 'jalepeno', 16: 'kiwi', 17: 'lemon', 18: 'lettuce',
          19: 'mango', 20: 'onion', 21: 'orange', 22: 'paprika', 23: 'pear', 24: 'peas', 25: 'pineapple',
          26: 'pomegranate', 27: 'potato', 28: 'raddish', 29: 'soy beans', 30: 'spinach', 31: 'sweetcorn',
          32: 'sweetpotato', 33: 'tomato', 34: 'turnip', 35: 'watermelon'}
sphereproduct = ['Apple','Banana', 'Bello Pepper', 'Chilli Pepper', 'Grapes', 'Jalepeno', 'Kiwi', 'Lemon', 'Orange',
                 'Paprika', 'Pear', 'Tomato', 'Pomegranate', 'Watermelon', 'Lettuce', 'Onion']

cylinderproduct = ['Beetroot', 'Cabbage', 'Capsicum', 'Carrot', 'Cauliflower', 'Corn', 'Cucumber', 'Eggplant', 'Ginger',
                   'Peas', 'Potato', 'Raddish', 'Soy Beans', 'Spinach', 'Sweetcorn', 'Sweetpotato', 'Mango',
                   'Turnip', 'Pineapple']

size_categories = {
    'Small': {'Spherical': (2, 3.5), 'elongated': (0.5, 2)},
    'Medium': {'Spherical': (3.5, 5), 'elongated': (2, 3.5)},
    'Large': {'Spherical': (5, 6.5), 'elongated': (3.5, 5)},
    'Extra-Large or Jumbo': {'Spherical': (6.5, float('inf')), 'elongated': (5, float('inf'))}
}

Builder.load_string('''
<cameraClick>:
    orientation: 'vertical'
    Camera:
        id: camera
        resolution: (640, 480)
        allow_stretch: True
        size_hint: (1,1)
        play: True

        canvas.before:
            PushMatrix
            Rotate:
                angle: -90
                origin: self.center
        canvas.after:
            PopMatrix


    Button:
        id: button
        text: 'Capture'
        size_hint_y: None
        height: '40dp'
        on_press: root.takepic()

''')

class ProductDisplay(GridLayout):
    def __init__(self, **kwargs):
        super(ProductDisplay, self).__init__(**kwargs)
        self.spacing = [30,0]  # Increase spacing between rows
        self.cols = 2  #  columns for: Product Name, Price
        self.size_hint_y=None
        self.show_grid = True  # Show grid lines
        self.bind(minimum_height=self.setter('height'))

    def add_product(self, product_name, product_price):

        self.product_label = Label(text=product_name,size_hint_y= None, text_size=self.size, valign='top',
                              halign='left')
        self.product_label.bind(size=self.product_label.setter('text_size'))  # Update text_size when label size changes

        self.product_price_label = Label(text=product_price, size_hint=(0.3, None), valign='top', halign='left')
        self.product_price_label.bind(size=self.product_price_label.setter('text_size'))

        self.add_widget(self.product_label)
        self.add_widget(self.product_price_label)

class NoMarkerPopup(Popup):
    def __init__(self, message, **kwargs):
        super(NoMarkerPopup, self).__init__(**kwargs)
        self.title = 'Warning'
        self.size_hint = (None, None)
        self.size = (300, 200)

        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=message))

        button = Button(text='OK')
        button.bind(on_release=self.dismiss)
        content.add_widget(button)

        self.content = content
class ConfirmationPopup(Popup):
    def __init__(self, text, callback, **kwargs):
        super(ConfirmationPopup, self).__init__(**kwargs)
        self.title = 'Confirmation'
        self.callback = callback

        layout = self.create_layout(text)
        self.content = layout
        self.size_hint = (None, None)  # Disable automatic sizing
        self.size = (300, 200)  # Set the size of the popup
    def create_layout(self, text):
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(Label(text=text))
        yes_button = Button(text='Yes', on_press=self.on_yes)
        no_button = Button(text='No', on_press=self.on_no)
        layout.add_widget(yes_button)
        layout.add_widget(no_button)
        return layout

    def on_yes(self, instance):
        self.callback(True)
        self.dismiss()

    def on_no(self, instance):
        self.dismiss()
        self.callback(False)
class TextInputPopup(Popup):
    def __init__(self, callback, **kwargs):
        super(TextInputPopup, self).__init__(**kwargs)
        self.title = 'Enter Correct Information'
        self.callback = callback

        self.text_input = TextInput()
        self.submit_button = Button(text='Submit', on_press=self.on_submit)

        layout = BoxLayout(orientation='vertical')
        layout.add_widget(self.text_input)
        layout.add_widget(self.submit_button)

        self.content = layout
        self.size_hint = (None, None)  # Disable automatic sizing
        self.size = (300, 200)  # Set the size of the popup

    def on_submit(self, instance):
        self.dismiss()
        self.callback(self.text_input.text)

class cameraClick(BoxLayout):
    def on_confirmation(self, confirmed):
        if confirmed:
            # self.dismiss()
            print("Proceed to next screen")
            # Code to proceed to next screen
        else:
            self.text_input_popup = TextInputPopup(callback=self.on_text_input)
            self.text_input_popup.open()
    def on_text_input(self, text):
        # self.res=text
        setattr(self.prod_label, "text", str(text))
        print("Correct information:", text)
    def switch(self,instance):
        price = self.prod_label.text

        # Create an instance of SecondScreen and pass the price as a parameter
        second_screen = SecondPage(price=price)

        # Add the instance to the ScreenManager
        myapp.screen_manager.add_widget(second_screen)

        # self.secondpage = SecondPage()
        # screen = Screen(name='Second')
        # screen.add_widget(self.secondpage)
        # self.screen_manager.add_widget(screen)

        # Switch to the second screen
        myapp.screen_manager.current = second_screen.name

    def takepic(self, *args):

        SAVE_PATH = 'img.png'

        self.web_cam = self.ids['camera']
        self.btn = self.ids['button']
        self.web_cam.export_to_png(os.path.join(os.getcwd(), SAVE_PATH))

        print("path", os.path.join(os.getcwd(), SAVE_PATH))

        # Load Image
        frame = cv2.imread(os.path.join(os.getcwd(), 'img.png'))
        print("path", os.path.join(os.getcwd(), 'img.png'))

        # Load Aruco detector
        parameters = cv2.aruco.DetectorParameters_create()
        aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_5X5_50)

        # Load Object Detector
        detector = HomogeneousBgDetector()

        # Get Aruco marker
        corners, _, _ = cv2.aruco.detectMarkers(frame, aruco_dict, parameters=parameters)

        if corners:
            # Draw polygon around the marker
            int_corners = np.int0(corners)
            cv2.polylines(frame, int_corners, True, (0, 255, 0), 5)

            # Aruco Perimeter
            aruco_perimeter = cv2.arcLength(corners[0], True)

            # Pixel to cm ratio
            pixel_cm_ratio = aruco_perimeter / 20

            # get all obj contour in img captured
            contours = detector.detect_objects(frame)

            # aruco marker
            x_min = int(min(corners[0][0][:, 0]))
            x_max = int(max(corners[0][0][:, 0]))
            y_min = int(min(corners[0][0][:, 1]))
            y_max = int(max(corners[0][0][:, 1]))

            largestArea=0

            # Draw objects boundaries
            for cnt in contours:
                rect = cv2.minAreaRect(cnt)
                (x, y), (w, h), angle = rect
                box = cv2.boxPoints(rect)
                box = np.int0(box)

                # contour coordinates
                x_min2 = np.min(box[:, 0])
                x_max2 = np.max(box[:, 0])
                y_min2 = np.min(box[:, 1])
                y_max2 = np.max(box[:, 1])

                #return only largest ctr except aruco
                if not (x_min-13<x_min2 and x_max+13>x_max2 and y_min-13<y_min2 and y_max+13>y_max2):  # if ctr is not aurco marker
                    area = cv2.contourArea(cnt)
                    if area>largestArea:
                        largestCtr=cnt
                else:
                    frameCut2 = frame[y_min - 13:y_max + 13, x_min - 13:x_max + 13]
                    # cv2.imshow("framearuco", frameCut2)

            # Get rect
            rect = cv2.minAreaRect(largestCtr)
            (x, y), (w, h), angle = rect

            # Get Width and Height of the Objects by applying the Ratio pixel to cm
            object_width = w / pixel_cm_ratio
            object_height = h / pixel_cm_ratio


            #diameter based largest dimensions
            if w>h:
                self.diameter = object_width
            else:
                self.diameter = object_height

            box = cv2.boxPoints(rect)
            box = np.int0(box)

            # contour detected
            x_min2 = np.min(box[:, 0])
            x_max2 = np.max(box[:, 0])
            y_min2 = np.min(box[:, 1])
            y_max2 = np.max(box[:, 1])

            frameCut = frame[y_min2:y_max2, x_min2:x_max2]
            # cv2.imshow("frameproductonly", frameCut)

            #save only img w/t aruco marker
            os.remove(os.path.join(os.getcwd(), SAVE_PATH))
            cv2.imwrite(os.path.join(os.getcwd(), SAVE_PATH),frameCut)

            # img = PIL.Image.open(os.path.join(os.getcwd(), 'img3.png'))

            #load the tflite model
            model = 'GrocRecogModel.tflite'
            model_to_pred = TensorFlowModel()
            model_to_pred.load(os.path.join(os.getcwd(), model))

            # Read image and predict
            img = PIL.Image.open(os.path.join(os.getcwd(), SAVE_PATH))
            img_arr = img.resize((224, 224))
            img_arr = np.array(img_arr, np.float32)
            img_arr = img_arr[:, :, :3] / 255.0
            img_arr = np.expand_dims(img_arr, [0])
            answer = model_to_pred.pred(img_arr)
            y_class = answer.argmax(axis=-1)
            ylabel = " ".join(str(x) for x in y_class)
            ylabel = int(ylabel)

            self.res = str(labels[ylabel])
            print("ml model", str(self.res))

            #confirming prod name with pop up, renew prod name if nt correct
            #check prod name in offered prod list
            self.info = "Is the product name: "+str(self.res)
            self.confirmation_popup = ConfirmationPopup(text=self.info, callback=self.on_confirmation)
            self.confirmation_popup.open()

            self.prod_label = Label(text=str(self.res), size_hint=(1, .1))

            if self.res in sphereproduct:
                object_volume = (4 / 3) * math.pi * (object_width / 2) ** 2
                self.shape="spherical"
            else:  # cylinder
                object_volume = object_height * math.pi * (object_width / 2) ** 2
                self.shape = "elongated"

            #get size based on shape and diameter (longest width/height)
            for category, ranges in size_categories.items():
                min_diameter, max_diameter = ranges[self.shape]
                if min_diameter <= self.diameter < max_diameter:
                    self.prodsize=category

            object_volume = round(object_volume, 3)
            print("volume", object_volume)
            self.prod_vol = Label(text=str(object_volume)+" cm [sup]3[/sup]" ,size_hint=(1, .1),markup=True)

            self.size_scale = Label(text=self.prodsize ,size_hint=(1, .1),markup=True)
            cv2.putText(frame, "Width {} cm".format(round(object_width, 2)), (int(x - 100), int(y - 40)),
                        cv2.FONT_HERSHEY_PLAIN, 1, (200, 200, 0), 2)
            cv2.putText(frame, "Height {} cm".format(round(object_height, 2)), (int(x - 100), int(y + 15)),
                        cv2.FONT_HERSHEY_PLAIN, 1, (200, 200, 0), 2)

            cv2.circle(frame, (int(x), int(y)), 4, (0, 0, 255), -1)
            cv2.polylines(frame, [box], True, (255, 0, 0), 2)

            buf = cv2.flip(frame, 0).tobytes()
            img_texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            img_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.remove_widget(self.web_cam)
            self.remove_widget(self.btn)
            # self.web_cam = Image(source=SAVE_PATH, size_hint=(1,1))
            self.cam_result = Image(size_hint=(1, 1),texture=img_texture)

            # self.web_cam.texture = img_texture
            self.nextbtn = Button(text="Next",background_color =(0, 0, 145, 0.8), size_hint_y= None,height= '50dp')
            self.nextbtn.bind(on_press=self.switch)

            self.add_widget(self.cam_result)
            self.add_widget(self.prod_label)
            self.add_widget(self.prod_vol)
            self.add_widget(self.size_scale)
            self.add_widget(self.nextbtn)

        else:
            message = "Aruco marker is not being captured!"
            popup = NoMarkerPopup(message=message)
            popup.open()
            print("no mark")

class SecondPage(Screen):
    def __init__(self, price, **kwargs):
        super(SecondPage, self).__init__(**kwargs)
        self.prodnametxt = price  # Set the price attribute

        def prodfilterprice(req, products_return):
            print(products_return)
            # setattr(self.prod_scraped, "text", str(products_return))

            scroll_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
            scroll_layout.bind(minimum_height=scroll_layout.setter('height'))

            product_display = None

            for index, item in enumerate(products_return):
                if isinstance(item, str):  # If it's a supermarket name
                    current_supermarket = item
                    product_display = ProductDisplay()
                    scroll_layout.add_widget(Label(text=current_supermarket, bold=True, size_hint_y=None, height=40, font_size=20))
                    scroll_layout.add_widget(product_display)

                else:  # If it's a product
                    if product_display:
                        product_display.add_product(item[0], item[1])
                    # if isinstance(products_return[index + 1], str):

            scroll_view = ScrollView()
            scroll_view.add_widget(scroll_layout)
            self.layout.add_widget(scroll_view)

        self.layout = BoxLayout(orientation='horizontal')

        self.prodname = Label(text=f"Product Name:\n{self.prodnametxt}", font_size=25, size=(2, 20))
        self.layout.add_widget(self.prodname)
        print(self.prodnametxt)

        UrlRequest("https://apifyp.azurewebsites.net/get/" + str(self.prodnametxt),
                   on_success=prodfilterprice)


        # Button to switch to previous screen
        button = Button(text="Previous")
        button.bind(on_press=self.switch_screen)

        self.add_widget(self.layout)
        # self.add_widget(button)

    def switch_screen(self, instance):
        myapp.screen_manager.current = "First"

class MyApp(App):
    def build(self):
        self.screen_manager = ScreenManager()
        self.sizepage = cameraClick()
        screen = Screen(name='First')
        screen.add_widget(self.sizepage)
        self.screen_manager.add_widget(screen)

        # self.secondpage = SecondPage()
        # screen = Screen(name='Second')
        # screen.add_widget(self.secondpage)
        # self.screen_manager.add_widget(screen)

        return self.screen_manager


if __name__ == '__main__':
    myapp = MyApp()
    myapp.run()





