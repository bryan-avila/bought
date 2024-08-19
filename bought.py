import ttkbootstrap as ttk
import pymongo
from ttkbootstrap.scrolled import ScrolledFrame
from typing import List
from PIL import Image, ImageTk
from tkinter import filedialog
from settings import *

# Establish connection to local MongoDB
my_client = pymongo.MongoClient("mongodb://localhost:27017/")
my_db = my_client['Bought']
my_collection = my_db['Purchases']

# Contains ttk.Style() stylings, as well as placing the Main and Bottom frame widgets.
class Bought(ttk.Window):
    def __init__(self):
        super().__init__()
        self.title('Bought')

        # Window Icon
        icon = Image.open('dollar.png')
        iconPhoto = ImageTk.PhotoImage(icon)
        self.wm_iconphoto(False, iconPhoto)
        
        # Sizing
        self.minsize(int(WINDOW_SIZE.split('x')[0]), int(WINDOW_SIZE.split('x')[1]))
        self.center_screen_launch(int(WINDOW_SIZE.split('x')[0]), int(WINDOW_SIZE.split('x')[1]))

        # Stylings
        ttk.Style().theme_use(APP_THEME)
        ttk.Style().configure('TButton', font=BUTTON_TEXT_FONT)
        ttk.Style().configure('TEntry', font=('Papyrus', 10))
        ttk.Style().configure(style='custom.TButton', background=EXPENSE_CARD_BUTTON_COLOR, foreground='white', font=('Lexend', 10))
        ttk.Style().configure(style='upload.TButton', background=EXPENSE_CARD_BUTTON_COLOR, foreground='white', font=('Verdana', 13))

        # Bindings
        self.bind('<Escape>', self.esc_exit)
        self.protocol("WM_DELETE_WINDOW", self.click_exit)

        # Create Widgets 
        self.main_frame = MainFrame(self)
        BottomFrame(self, self.main_frame)
        self.validate_mongodb() # If data exists in local MongoDB, create the approriate widgets.

        # Run the App!
        self.mainloop()

    def center_screen_launch(self, width, height):
        window_width = width
        window_height = height

        user_display_width = self.winfo_screenwidth()
        user_display_height = self.winfo_screenheight()

        left_position = int(user_display_width / 2 - window_width / 2)
        top_position = int(user_display_height / 2 - window_height / 2)

        self.geometry(f'{window_width}x{window_height}+{left_position}+{top_position}')

    def validate_mongodb(self):
        # Check if the collection actually exists!
        if (my_db.list_collection_names()):
            # Iterate through each document.
            print("MongoDB data found! Creating ExpenseCards and placing them in MainFrame....")

            for document in my_collection.find({}, {"_id": 0}):
                mongo_entries: List[str] = [] 
                for key, item in document.items():
                    mongo_entries.append(item)
                # Create an ExpenseCard for each document!
                ExpenseCard(self.main_frame, mongo_entries[0], str(mongo_entries[1]), mongo_entries[2], True)
        else:
            print("No MongoDB data found. Starting application with no ExpenseCards....")
    
    def click_exit(self):
        print("Disconnecting from MongoDB thru mouse click and closing app....")
        my_client.close()
        self.destroy()
    
    def esc_exit(self, event):
        print("Disconnecting from MongoDB thru ESC and closing app....")
        my_client.close()
        self.destroy()


# Main Frame takes up 90% of the window screen. Uses that space to display ExpenseCards/Summary. Allows Scrolling.
class MainFrame(ScrolledFrame):
    def __init__(self, master):
        super().__init__(master, autohide=True)
        self.place(relx=0, rely=0, relwidth=1, relheight=0.90)


# Bottom Frame takes up 10% of the window screen. 
# Is given access to MainFrame in order to display EntryFrame and create ExpenseCards.
# Uploads data to MongoDB
# Sorts ExpenseCards by Price.
# Has a button to display an ExpenseSummary.
# Holds the logic for 'switching' screens!
class BottomFrame(ttk.Frame):
    def __init__(self, master, main_frame):
        self.master = master
        self.main_frame = main_frame # Access to Main Frame!
        super().__init__(master)
        self.place(relx=0, rely=1, relwidth=1, relheight=0.10, anchor='sw')
        self.create_widgets()


    # Create Add Expense, Sort and Summary Buttons and place them.
    def create_widgets(self):
        self.add_expense_button = ttk.Button(master=self, text='Add Expense', takefocus=False, command=self.display_entry_frame)
        self.add_expense_button.place(relx=0.5, rely=1, relheight=0.8, relwidth=0.2, anchor='s')

        self.sort_expenses_button = ttk.Button(master=self, text='Sort', takefocus=False, command=self.sort_expense_cards)
        self.sort_expenses_button.place(relx=0, rely=0.2, relheight=0.8, relwidth=0.2)

        self.summary_button = ttk.Button(master=self, text='Expense Summary', takefocus=False, command=self.sum_expenses)
        self.summary_button.place(relx=0.8, rely=0.2, relheight=0.8, relwidth=0.2)


    def display_entry_frame(self):
        self.entry_frame = EntryFrame(self.master)
        self.configure_bottom_buttons('confirm')


    def create_expense_card(self):
        self.entry_frame.place_forget() 
        entries_list = self.entry_frame.return_entries()
        
        # Error check. Only create ExpenseCard if ALL entries filled.
        if entries_list[0] == '' or not entries_list[1] or not entries_list[2]:
            print("ERROR! One or more entries were not entered. Returning to Main Frame...")
            self.configure_bottom_buttons('add')

        else: # If NO error, then upload entry data to MongoDB and then create ExpenseCard.
            print("Success! Creating an ExpenseCard and packing it within Main Frame...")
            self.upload_to_mongodb(entries_list[0], entries_list[1], entries_list[2])
            ExpenseCard(self.main_frame, entries_list[0], entries_list[1], entries_list[2], True)
            self.configure_bottom_buttons('add')


    def sort_expense_cards(self):
        # Clear main frame!
        print("Sorting Expense Cards by Price. Clearing Main Frame...")
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Sort using pymongo and populate MainFrame with ExpenseCards.
        sorted_docs = my_collection.find({}, {"_id": 0}).sort('amount', pymongo.ASCENDING)
        for document in sorted_docs:
            mongo_sorted_entries: List[str] = []
            for key, item in document.items():
                mongo_sorted_entries.append(item)
            ExpenseCard(self.main_frame, str(mongo_sorted_entries[0]), str(mongo_sorted_entries[1]), str(mongo_sorted_entries[2]), True)
        
        print("Finished Sorting! Displaying ExpenseCards...")


    def sum_expenses(self):
        # Change button states and summary button command.
        self.configure_bottom_buttons('go_back')

        # Create a pipeline that finds the sum of 'amount' for ALL documents in collection!
        result = my_collection.aggregate([ 
                                            {'$group': 
                                                    {"_id": None, 
                                                     "total": {"$sum": '$amount'}
                                                    }
                                                }
                                            ])
        for document in result:
            for key, item in document.items():
                if key == 'total':
                    self.sum_amount = round(float(item), 2)

        # Find the total amount of expenses. 
        self.expense_count = my_collection.count_documents({})

        # Find the most Expensive purchase yet.
        sorted_docs = my_collection.find({}, {"_id": 0}).sort('amount', pymongo.DESCENDING)
        largest_expense: List[str] = []
        for document in sorted_docs:
            for key, item in document.items():
                largest_expense.append(item)
            break

        # Display Expense Summary!
        self.expense_summary = ExpenseSummary(self.master, self.sum_amount, self.expense_count, largest_expense[0], largest_expense[1], largest_expense[2])


    def return_to_main(self):
        self.configure_bottom_buttons('summary')
        self.expense_summary.place_forget()


    def configure_bottom_buttons(self, state):
        # Config Add Expense Button to 'display entry frame' command. Re-enable sort and summary buttons. 
        if state == 'add':
            self.add_expense_button.configure(text='Add Expense', command=self.display_entry_frame)
            self.sort_expenses_button.state(["!disabled"])
            self.summary_button.state(["!disabled"])

        # Config Add Expense Button to 'create expense card' command. Disable sort and summary buttons.
        elif state == 'confirm': 
            self.add_expense_button.configure(text='Confirm Expense', command=self.create_expense_card)
            self.sort_expenses_button.state(["disabled"])
            self.summary_button.state(["disabled"])

        # Config Summary Button to 'return to main' command. Disable sort and add buttons. 
        elif state == 'go_back':
            self.summary_button.configure(text="Go Back", command=self.return_to_main)
            self.sort_expenses_button.state(["disabled"])
            self.add_expense_button.state(["disabled"])

        # Config Summary Button to 'display expense' command. Re-enable sort and add buttons. 
        elif state =='summary':
            self.summary_button.configure(text="Expense Summary", command=self.sum_expenses)
            self.sort_expenses_button.state(["!disabled"])
            self.add_expense_button.state(["!disabled"])


    # Upload AMOUNT as a FLOAT
    def upload_to_mongodb(self, image_path, amount, date):
        my_collection.insert_one({"image_path": image_path, "amount": float(amount), "date": date})


# Entry Frame contains an upload and two entry widgets. That data will be placed on a list. 
class EntryFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.place(relx=0, rely=0, relwidth=1, relheight=0.90)

        # Row/Column Config
        self.rowconfigure(0, weight=1, uniform='a')
        self.rowconfigure(1, weight=1, uniform='a')
        self.rowconfigure(2, weight=1, uniform='a')
        self.rowconfigure(3, weight=1, uniform='a')
        self.rowconfigure(4, weight=1, uniform='a')
        self.columnconfigure(0, weight=1, uniform='frank')
        self.columnconfigure(1, weight=1, uniform='frank') # arbitrary grouping name
        self.columnconfigure(2, weight=1, uniform='frank')
        self.columnconfigure(3, weight=1, uniform='frank')
        self.columnconfigure(4, weight=1, uniform='frank')

        self.create_widgets()

    def create_widgets(self):
        self.amount_variable = ttk.StringVar()
        self.date_variable = ttk.StringVar()
        self.image_path = '' # Initially empty until an image is chosen

        self.upload_label = ttk.Label(master=self, text='Receipt/Proof of Purchase ', font=LABEL_TEXT_FONT)
        self.upload_label.grid(row=1, column=0, columnspan=2, padx=10)

        self.upload_button = ttk.Button(master=self, text='Upload Image', takefocus=False, command=self.upload_image)
        self.upload_button.grid(row=2, column=0, columnspan=2, sticky='nsew', padx=10)

        self.amount_label = ttk.Label(master=self, text='Enter Total Amount ', font=LABEL_TEXT_FONT)
        self.amount_label.grid(row=1, column=2, padx=10)

        self.amount_entry = ttk.Entry(master=self, style=ttk.INFO, font=ENTRY_TEXT_FONT, justify='center', textvariable=self.amount_variable)
        self.amount_entry.grid(row=2, column=2, sticky='nsew', padx=10)

        self.date_label = ttk.Label(master=self, text='Enter Date of Expense ', font=LABEL_TEXT_FONT)
        self.date_label.grid(row=1, column=3, columnspan=2, padx=10)

        self.date_entry = ttk.Entry(master=self, style=ttk.INFO, font=ENTRY_TEXT_FONT, justify='center', textvariable=self.date_variable)
        self.date_entry.grid(row=2, column=3,  columnspan=2, sticky='nsew', padx=10)

    def return_entries(self):
        # This method is used within BottomFrame to create an ExpenseCard!
        entries: List[str] = [self.image_path, self.amount_variable.get(), self.date_variable.get()]
        return entries 
    
    def upload_image(self):
        self.image_path = filedialog.askopenfile().name
        self.upload_button.configure(text='Image Uploaded', style='upload.TButton')


# ExpenseCard is initialized with the data from an EntryFrame's data list or from mongoDB data.  
class ExpenseCard(ttk.Frame):
    def __init__(self, master, image_path, amount, date, deletion_status):
        super().__init__(master)
        self.pack(side='top', expand=True, fill='both', pady=10)

        # Variables for mongodb deletion
        self.this_image_path = image_path
        self.this_amount = amount
        self.this_date = date

        # Row/Column Config
        self.columnconfigure(0, weight=5, uniform='a')
        self.columnconfigure(1, weight=3, uniform='greg') # arbitrary name used to group 
        self.columnconfigure(2, weight=1, uniform='greg')
        self.rowconfigure(0, weight=1, uniform='a')
        self.rowconfigure(1, weight=1, uniform='a')

        self.create_widgets(image_path, amount, date, deletion_status)

    def create_widgets(self, image_path, amount, date, deletion_status):
        self.receipt_canvas = ImageContainer(self, image_path, 'allow_zoom')
    
        self.amount_label = ttk.Label(master=self, text="TOTAL COST: $" + str(amount), font=LABEL_TEXT_FONT, background=EXPENSE_BACKGROUND_COLOR, foreground='white', anchor='center', borderwidth=5, relief='ridge')
        self.amount_label.grid(column=1, row=0, sticky='nsew', padx=3)

        self.date_label = ttk.Label(master=self, text="DATE OF PURCHASE: " + date, font=LABEL_TEXT_FONT, background=EXPENSE_BACKGROUND_COLOR, foreground='white', anchor='center', borderwidth=5, relief='ridge')
        self.date_label.grid(column=1, row=1, sticky='nsew', padx=3)

        # Unless created for an ExpenseSummary, ExpenseCard will have a button to allow for deletion!
        if deletion_status is True: 
         self.delete_button = ttk.Button(master=self, text='Delete', style='custom.TButton', command=self.delete_card)
         self.delete_button.grid(column=2, row=0, sticky='nw')
        else:
            self.amount_label.grid(column=1, row=0, columnspan=2, sticky='nsew', padx=3)
            self.date_label.grid(column=1, row=1, columnspan=2, sticky='nsew', padx=3)

    # Allow this instance of ExpenseCard to be removed from the widget stack. Remove from mongoDB. 
    def delete_card(self):
        print("Removing ExpenseCard data from MongoDb....")
        my_collection.delete_one({"image_path": self.this_image_path, "amount": float(self.this_amount), "date": self.this_date})

        print("Removing ExpenseCard from screen....")
        self.pack_forget()


# ExpenseSummary holds labels with sum, count of expenses, and an ExpenseCard of the largest purchase.
class ExpenseSummary(ttk.Frame):
    def __init__(self, master, sum, count, image_path, amount, date):
        super().__init__(master)
        self.place(relx=0, rely=0, relwidth=1, relheight=0.90)

        # Create Widgets and pack them
        ttk.Label(master=self, text='Total Sum: $' + str(sum), font=SUMMARY_LABEL_FONT, background=EXPENSE_BACKGROUND_COLOR_2, borderwidth=5, relief='ridge').pack(side='top', expand=True, fill='both', pady=(0,10))
        ttk.Label(master=self,text='Number of Expenses: ' + str(count), font=SUMMARY_LABEL_FONT, background=EXPENSE_BACKGROUND_COLOR_2, borderwidth=5, relief='ridge').pack(side='top', fill='both', expand=True, pady=(0, 10))
        ttk.Label(master=self, text='Largest Purchase: ', font=('Lexend', 20), background=EXPENSE_BACKGROUND_COLOR_2, borderwidth=5, relief='ridge', anchor='center').pack(side='left', expand=True, fill='both', padx=(0, 12))
        ExpenseCard(self, str(image_path), str(amount), str(date), False)


# ImageContainer is a Canvas that holds an ImageTk. Clicking on the Canvas will bring up a top level window for a closer view of the image. 
class ImageContainer(ttk.Canvas):
    def __init__(self, master, image_path, zoom_option):
        super().__init__(master, borderwidth=5, relief='ridge')
        self.grid(row=0, column=0, rowspan=2, sticky='nsew')

        if zoom_option == 'allow_zoom':
            self.bind('<Button-1>', self.create_receipt_window) # Bind Mouse1 Click to get the full image.
        self.bind('<Configure>', self.resize_image) # Bind window adjustments to resizing the window.

        # image_path was passed from EntryFrame. Use that path to create an Image. 
        self.image_path = image_path
        self.image = Image.open(self.image_path)
        self.image_ratio = self.image.size[0] / self.image.size[1]
        self.image_tk = ImageTk.PhotoImage(self.image)

    def resize_image(self, event):

        # Grab canvas ratio, and compare it against the image's ratio. Adjust the
        # image's width and height accordingly. Clear the canvas and display the adjisted image. 
        # CREDIT: Thanks to Clear Code for guiding the entire ImageContainer code process! 
        # LINK: https://youtu.be/mop6g-c5HEY?si=NNGBttziY8uU8Yeq&t=56780
        self.canvas_ratio = event.width / event.height

        if self.canvas_ratio > self.image_ratio:
            self.image_height = int(event.height)
            self.image_width = int(self.image_height * self.image_ratio)
        else:
            self.image_width = int(event.width)
            self.image_height = int(self.image_width / self.image_ratio)

        self.delete('all')
        self.adjusted_image = self.image.resize((self.image_width, self.image_height))
        self.image_tk = ImageTk.PhotoImage(self.adjusted_image)
        self.create_image(event.width / 2 , event.height / 2, image=self.image_tk)
        self.configure(bg=EXPENSE_BACKGROUND_COLOR)

    def create_receipt_window(self, event):
        ReceiptWindow(self.image_path, 'no_zoom')


# ReceiptWindow will contain only an ImageContainer.
class ReceiptWindow(ttk.Toplevel):
    def __init__(self, image_path, no_zoom):
        super().__init__(topmost=True)
        self.geometry('1200x700')
        self.title('Receipt Viewer')
        icon = Image.open('zoom.png')
        iconPhoto = ImageTk.PhotoImage(icon)
        self.wm_iconphoto(False, iconPhoto)

        self.bind('<Escape>', lambda event: self.destroy())

        # Display only an Image in a 1x1 grid.
        self.rowconfigure(0, weight=1, uniform='a')
        self.columnconfigure(0, weight=1, uniform='a')
        ImageContainer(self, image_path, zoom_option=no_zoom)


Bought()