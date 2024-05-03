import cv2
import math
from object_detector import *
import numpy as np
from android_permissions import AndroidPermissions
import os
from model import TensorFlowModel
from kivy.properties import ObjectProperty
import PIL.Image
from camera4kivy import Preview
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.graphics import Rectangle, Line
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.graphics.texture import Texture
from kivy.uix.camera import Camera
from kivy.network.urlrequest import UrlRequest
from kivy.graphics import PushMatrix, PopMatrix, Rotate
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.scrollview import ScrollView
from toast import Toast

# Initialize variables
labels = {0: 'apple', 1: 'banana', 2: 'beetroot', 3: 'bell pepper', 4: 'cabbage', 5: 'capsicum', 6: 'carrot',
          7: 'cauliflower', 8: 'chilli pepper', 9: 'corn', 10: 'cucumber', 11: 'eggplant', 12: 'garlic', 13: 'ginger',
          14: 'grapes', 15: 'jalepeno', 16: 'kiwi', 17: 'lemon', 18: 'lettuce',
          19: 'mango', 20: 'onion', 21: 'orange', 22: 'paprika', 23: 'pear', 24: 'peas', 25: 'pineapple',
          26: 'pomegranate', 27: 'potato', 28: 'raddish', 29: 'soy beans', 30: 'spinach', 31: 'sweetcorn',
          32: 'sweetpotato', 33: 'tomato', 34: 'turnip', 35: 'watermelon'}
sphereproduct = ['apple', 'banana', 'bello pepper', 'chilli pepper', 'grapes', 'jalepeno', 'kiwi', 'lemon', 'orange',
                 'paprika', 'pear', 'tomato', 'pomegranate', 'watermelon', 'lettuce', 'onion']

cylinderproduct = ['beetroot', 'cabbage', 'capsicum', 'carrot', 'cauliflower', 'corn', 'cucumber', 'eggplant', 'ginger',
                   'peas', 'potato', 'raddish', 'soy beans', 'spinach', 'sweetcorn', 'sweetpotato', 'mango',
                   'turnip', 'pineapple']

size_categories = {
    'Small': {'spherical': (2.08, 9.35), 'elongated': (0.27, 2.54)},
    'Medium': {'spherical': (9.35, 10.62), 'elongated': (2.54, 3.81)},
    'Large': {'spherical': (10.62, 111.89), 'elongated': (3.81, 5.08)},
    'Extra-Large or Jumbo': {'spherical': (11.89, float('inf')), 'elongated': (5.08, float('inf'))}
}

Builder.load_string("""
<cameraClick>:
    orientation: 'vertical'

    Preview:
        id: preview
        size_hint: (1,1)

    Button:
        id: button
        text: 'Capture'
        size_hint_y: None
        height: '40dp'
        on_press: root.takepic()

    Button:
        id: nextcamera
        text: 'Check Result'
        size_hint_y: None
        height: '40dp'
        on_press: root.picresult()
""")


class ProductDisplay(GridLayout):
    def __init__(self, **kwargs):
        super(ProductDisplay, self).__init__(**kwargs)
        self.spacing = [30, 5]
        self.cols = 2  # columns for: Product Name, Price
        self.size_hint_y = None
        self.show_grid = True
        self.bind(minimum_height=self.setter('height'))

    def add_product(self, product_name, product_price):
        self.product_label = Label(text=product_name, size_hint_y=None, text_size=self.size, valign='top',
                                   halign='left')
        self.product_label.bind(size=self.product_label.setter('text_size'))

        self.product_price_label = Label(text=product_price, size_hint=(0.3, None), valign='top', halign='left')
        self.product_price_label.bind(size=self.product_price_label.setter('text_size'))

        self.add_widget(self.product_label)
        self.add_widget(self.product_price_label)


class NoMarkerPopup(Popup):
    def __init__(self, message, **kwargs):
        super(NoMarkerPopup, self).__init__(**kwargs)
        self.title = 'Warning'
        self.size_hint = (.3, .3)

        content = BoxLayout(orientation='vertical')
        self.warningmsg = Label(text=message, font_size='30', valign='middle')
        self.warningmsg.bind(size=self.warningmsg.setter('text_size'))
        content.add_widget(self.warningmsg)

        button = Button(text='OK', size_hint_y=None, height='40dp')
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
        self.size_hint = (.5, .4)

    def create_layout(self, text):
        layout = BoxLayout(orientation='vertical')
        self.confirmmsg = Label(text=text, valign='middle')
        self.confirmmsg.bind(size=self.confirmmsg.setter('text_size'))

        layout.add_widget(self.confirmmsg)
        yes_button = Button(text='Yes', on_press=self.on_yes, size_hint_y=None, height='40dp')
        no_button = Button(text='No', on_press=self.on_no, size_hint_y=None, height='40dp')
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
        self.submit_button = Button(text='Submit', on_press=self.on_submit,valign='middle',halign='center')
        # self.text_input.bind(size=self.text_input.setter('text_size'))
        self.submit_button.bind(size=self.submit_button.setter('text_size'))

        layout = BoxLayout(orientation='vertical')
        layout.add_widget(self.text_input)
        layout.add_widget(self.submit_button)

        self.content = layout
        self.size_hint = (.5, .4)
    def on_submit(self, instance):
        self.dismiss()
        self.callback(self.text_input.text)

class cameraClick(BoxLayout):
    def __init__(self, **args):
        super().__init__(**args)
        self.ids.preview.connect_camera(filepath_callback= self.capture_path)
    def capture_path(self,file_path):
        Toast().show(file_path)
    def on_confirmation(self, confirmed):
        if confirmed:
            print("Proceed to next screen")
        else:
            self.text_input_popup = TextInputPopup(callback=self.on_text_input)
            self.text_input_popup.open()

    def on_text_input(self, text):
        self.res = text
        print("Correct information:", text)
        setattr(self.prod_label, "text", str(text))
        self.sizeshapeGrade(text)

    def sizeshapeGrade(self, res):
        if res in sphereproduct:
            self.object_volume = (4 / 3) * math.pi * (self.object_width / 2) ** 2
            self.shape = "spherical"
        else:  # cylinder
            self.object_volume = self.object_height * math.pi * (self.object_width / 2) ** 2
            self.shape = "elongated"
        print(self.shape)
        print(self.diameter)
        # get size based on shape and diameter (longest width/height)
        for category, ranges in size_categories.items():
            min_diameter, max_diameter = ranges[self.shape]
            if min_diameter <= self.diameter < max_diameter:
                self.prodsize = category

        self.object_volume = round(self.object_volume, 3)
        print("volume", self.object_volume)
        print("prodsize", self.prodsize)
        setattr(self.prod_vol, "text", str(self.object_volume) + " cm [sup]3[/sup]")
        setattr(self.size_scale, "text", self.prodsize)

    def switch(self, instance):
        self.web_cam.disconnect_camera()
        price = self.prod_label.text
        # Create an instance of SecondScreen and pass the price as a parameter
        second_screen = SecondPage(price=price)
        myapp.screen_manager.add_widget(second_screen)
        myapp.screen_manager.current = second_screen.name

    def picresult(self):
        SAVE_PATH = "img.jpg"
        SUB_DIR = "photoApp"
        self.web_cam = self.ids['preview']
        self.btn = self.ids['button']
        self.btn2 = self.ids['nextcamera']
        frameSave = cv2.imread("/storage/emulated/0/DCIM/My Application/photoApp/img.jpg")
        frame = cv2.resize(frameSave, (480, 640))
        print("path1",os.path.join(os.getcwd(), SAVE_PATH))

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

            largestArea = 0
            largestCtr = contours[0]
            # return only largest ctr except aruco
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
                if x_min2 < 0 or x_max2 < 0 or y_min2 < 0 or y_max2 < 0:
                    break

                if not (x_min - 20 < x_min2 and x_max + 20 > x_max2 and
                        y_min - 20 < y_min2 and y_max + 20 > y_max2):  # if ctr is not aurco marker
                    if w * h > largestArea:
                        largestCtr = cnt

            rect = cv2.minAreaRect(largestCtr)
            (x, y), (w, h), angle = rect

            # Get Width and Height of the Objects by applying the Ratio pixel to cm
            self.object_width = w / pixel_cm_ratio
            self.object_height = h / pixel_cm_ratio
            print(self.object_width)
            print(self.object_height)

            # diameter based on largest dimensions
            if w > h:
                self.diameter = self.object_height
            else:
                self.diameter = self.object_width

            box = cv2.boxPoints(rect)
            box = np.int0(box)

            # contour detected
            x_min2 = np.min(box[:, 0])
            x_max2 = np.max(box[:, 0])
            y_min2 = np.min(box[:, 1])
            y_max2 = np.max(box[:, 1])

            #frameCut = frame[y_min2-5:y_max2+5, x_min2-5:x_max2+5]

            # save only img w/t aruco marker
            # os.remove(os.path.join(os.getcwd(), SUB_DIR, SAVE_PATH))
            cv2.imwrite(os.path.join(os.getcwd(), SAVE_PATH), frameSave)

            # load the tflite model
            model = 'GrocRecogModel.tflite'
            model_to_pred = TensorFlowModel()
            model_to_pred.load(os.path.join(os.getcwd(), model))
            print("path", os.path.join(os.getcwd(), SAVE_PATH))
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

            # confirming prod name with pop up, renew prod name if nt correct
            self.info = "Is the product name: " + str(self.res)
            self.confirmation_popup = ConfirmationPopup(text=self.info, callback=self.on_confirmation)
            self.confirmation_popup.open()
            self.prod_label = Label(text=str(self.res), size_hint=(1, .1))

            self.prod_vol = Label(text="", size_hint=(1, .1), markup=True)
            self.size_scale = Label(text="", size_hint=(1, .1), markup=True)

            self.sizeshapeGrade(self.res)

            cv2.putText(frame, "Width {} cm".format(round(self.object_width, 2)), (int(x - 100), int(y - 40)),
                        cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0), 1)
            cv2.putText(frame, "Height {} cm".format(round(self.object_height, 2)), (int(x - 100), int(y + 30)),
                        cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0), 1)

            cv2.circle(frame, (int(x), int(y)), 6, (0, 0, 255), -1)
            cv2.polylines(frame, [box], True, (255, 0, 0), 8)
            
            frame = cv2.resize(frame, (960, 1280))
            rgb_image = cv2.cvtColor(cv2.flip(frame, 0), cv2.COLOR_BGR2RGB)
            pil_image = PIL.Image.fromarray(rgb_image)
            img_texture = Texture.create(size=pil_image.size, colorfmt='rgb')
            img_texture.blit_buffer(pil_image.tobytes(), colorfmt='rgb', bufferfmt='ubyte')

            self.remove_widget(self.web_cam)
            self.remove_widget(self.btn)
            self.remove_widget(self.btn2)
            self.cam_result = Image(size_hint=(1, 1), texture=img_texture)

            self.nextbtn = Button(text="Next", size_hint_y=None, height='50dp')
            self.nextbtn.bind(on_press=self.switch)

            self.add_widget(self.cam_result)
            self.add_widget(self.prod_label)
            self.add_widget(self.prod_vol)
            self.add_widget(self.size_scale)
            self.add_widget(self.nextbtn)

        else:
            message = "Unable to Capture Aruco marker!"
            popup = NoMarkerPopup(message=message)
            popup.open()
            print("no mark")

    def takepic(self, *args):
        try:
            os.remove("/storage/emulated/0/DCIM/My Application/photoApp/img.jpg")
        except:
            pass
        SAVE_PATH = "img.jpg"
        SUB_DIR = "photoApp"
        self.web_cam = self.ids['preview']
        self.web_cam.capture_photo(subdir=SUB_DIR, name=SAVE_PATH)


class SecondPage(Screen):
    def __init__(self, price, **kwargs):
        super(SecondPage, self).__init__(**kwargs)
        self.prodnametxt = price  # Set the price attribute

        def prodfilterprice(req, products_return):
            print(products_return)

            scroll_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
            scroll_layout.bind(minimum_height=scroll_layout.setter('height'))

            product_display = None

            for index, item in enumerate(products_return):
                if isinstance(item, str):  # If it's a supermarket name
                    current_supermarket = item
                    product_display = ProductDisplay()
                    scroll_layout.add_widget(
                        Label(text=current_supermarket, bold=True, size_hint_y=None, height=40, font_size=50))
                    scroll_layout.add_widget(product_display)

                else:  # If it's a product
                    if product_display:
                        product_display.add_product(item[0], item[1])
                    # if isinstance(products_return[index + 1], str):

            scroll_view = ScrollView()
            scroll_view.add_widget(scroll_layout)
            self.layout.add_widget(scroll_view)

        self.leftlayout = BoxLayout(orientation='vertical', size_hint_x=0.3)

        self.layout = BoxLayout(orientation='horizontal', spacing=10)

        # Button to switch to previous screen
        self.button = Button(text="Previous", size_hint_y=None, height='50dp')
        self.button.bind(on_press=self.switch_screen)

        self.prodname = Label(text=f"Product Name:\n{self.prodnametxt}", font_size=30, valign='middle',halign='center')  # size=(2, 20))
        self.prodname.bind(size=self.prodname.setter('text_size'))

        print(self.prodnametxt)
        self.leftlayout.add_widget(self.prodname)
        self.leftlayout.add_widget(self.button)

        self.layout.add_widget(self.leftlayout)

        UrlRequest("https://apifyp.azurewebsites.net/get/" + str(self.prodnametxt),
                   on_success=prodfilterprice)

        self.add_widget(self.layout)

    def switch_screen(self, instance):
        myapp.screen_manager.current = "First"


class MyApp(App):
    def build(self):
        self.screen_manager = ScreenManager()

        self.sizepage = cameraClick()
        # self.sizepage = PhotoScreen1()
        screen = Screen(name='First')
        screen.add_widget(self.sizepage)
        self.screen_manager.add_widget(screen)

        return self.screen_manager

    def on_start(self):
        self.dont_gc = AndroidPermissions(self.start_app)

    def start_app(self):
        self.dont_gc = None


if __name__ == '__main__':
    myapp = MyApp()
    myapp.run()





