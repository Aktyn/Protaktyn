from typing import Optional
from src.common.utils import use_epaper

if use_epaper():
    import os

    from waveshare_epd import epd4in2
    from PIL import Image, ImageDraw, ImageFont


    class EPaper:
        class __DisplayMode:
            FULL = 0
            PARTIAL = 1

        def __init__(self):
            self.__mode = None

            res_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
                                   'res')
            self.__font = ImageFont.truetype(os.path.join(res_dir, 'RobotoMono-Medium.ttf'), 128)
            self.__font_small = ImageFont.truetype(os.path.join(res_dir, 'RobotoMono-Medium.ttf'), 48)
            self.__current_points: tuple[Optional[int], Optional[int]] = (None, None)
            self.__current_set_points: tuple[Optional[int], Optional[int]] = (None, None)

            self.__epd = epd4in2.EPD()
            self.clear()

            self.__logo_image = Image.open(os.path.join(res_dir, 'logo.jpg'))
            self.__logo_image = self.__logo_image.resize((96, 96))

            self.__image = Image.new('1', (self.__epd.width, self.__epd.height), 0)  # 255
            self.__draw = ImageDraw.Draw(self.__image)

            self.__draw_clear()
            self.__draw_logo()
            self.__epd.display(self.__epd.getbuffer(self.__image))
            self.update_points(0, 0)
            self.update_set_points(0, 0)

        def close(self):
            print("Putting e-paper display to sleep...")
            self.__epd.sleep()

        def clear(self):
            print("Clearing e-paper display...")
            self.__set_mode(self.__DisplayMode.FULL)
            self.__epd.Clear()

        def __set_mode(self, mode: int):
            if self.__mode == mode:
                return
            self.__mode = mode
            if mode == self.__DisplayMode.FULL:
                self.__epd.init()
            elif mode == self.__DisplayMode.PARTIAL:
                self.__epd.init_Partial()

        def display_text(self, text: str):
            self.__set_mode(self.__DisplayMode.FULL)
            self.__draw_clear()
            self.__draw.text((self.__epd.width / 2, self.__epd.height / 2), text, font=self.__font, fill=0, anchor="mm")
            self.__epd.display(self.__epd.getbuffer(self.__image))

        def __draw_clear(self, x_start=0, y_start=0, x_end: Optional[int] = None, y_end: Optional[int] = None,
                         color=255):
            self.__draw.rectangle((x_start, y_start, x_end or self.__epd.width, y_end or self.__epd.height), fill=color)

        def __draw_logo(self):
            self.__image.paste(self.__logo_image, (int((self.__image.width - self.__logo_image.width) / 2), 8))

        @staticmethod
        def __format_points(points: tuple[Optional[int], Optional[int]]):
            p1, p2 = points
            if (p2 or 0) < 10:
                p2 = str(p2 or 0) + " "
            p1 = p1 or 0 if (p1 or 0) >= 10 else " " + str(p1 or 0)
            return f"{p1}|{p2}"

        def __draw_points(self):
            text = self.__format_points(self.__current_points)
            self.__draw.text((self.__epd.width / 2, self.__epd.height / 2), text, font=self.__font, fill=0,
                             anchor="mm")

        def __draw_set_points(self):
            text = self.__format_points(self.__current_set_points)
            self.__draw.text((self.__epd.width / 2, self.__epd.height), text, font=self.__font_small, fill=0,
                             anchor="mb")

        def update_points(self, p1: int, p2: int):
            p1_differs = p1 != self.__current_points[0]
            p2_differs = p2 != self.__current_points[1]
            if not p1_differs and not p2_differs:
                return
            self.__set_mode(self.__DisplayMode.PARTIAL)
            self.__current_points = (p1, p2)

            x_start = 0 if p1_differs else int(self.__epd.width / 2)
            y_start = 100
            x_end = self.__epd.width if p2_differs else int(self.__epd.width / 2)
            y_end = 200  # no more than self.__epd.height which is 300

            self.__draw_clear(x_start=x_start, y_start=y_start, x_end=x_end, y_end=y_end)
            self.__draw_points()

            self.__epd.EPD_4IN2_PartialDisplay(x_start, y_start, x_end, y_end, self.__epd.getbuffer(self.__image))

        def update_set_points(self, p1: int, p2: int):
            p1_differs = p1 != self.__current_set_points[0]
            p2_differs = p2 != self.__current_set_points[1]
            if not p1_differs and not p2_differs:
                return
            self.__set_mode(self.__DisplayMode.PARTIAL)
            self.__current_set_points = (p1, p2)

            x_start = 0 if p1_differs else int(self.__epd.width / 2)
            y_start = 200
            x_end = self.__epd.width if p2_differs else int(self.__epd.width / 2)
            y_end = self.__epd.height

            self.__draw_clear(x_start=x_start, y_start=y_start, x_end=x_end, y_end=y_end)
            self.__draw_set_points()

            self.__epd.EPD_4IN2_PartialDisplay(x_start, y_start, x_end, y_end, self.__epd.getbuffer(self.__image))

else:
    class EPaper:
        def __init__(self):
            pass

        def close(self):
            pass

        def clear(self):
            pass

        def display_text(self, _: str):
            pass

        def update_points(self, _: int, __: int):
            pass

        def update_set_points(self, _: int, __: int):
            pass
