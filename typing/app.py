import time
import pdb
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject

class TypingWindow(Gtk.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_default_size(-1, 350)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.add(vbox)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(hbox, False, False, 0)

        button = Gtk.Button.new_with_label("Load text from file")
        button.connect("clicked", self.on_load_clicked)
        hbox.pack_start(button, True, True, 0)

        button = Gtk.Button.new_with_label("Paste text")
        button.connect("clicked", self.on_paste_clicked)
        hbox.pack_start(button, True, True, 0)
        
        button = Gtk.Button.new_with_label("Start again")
        button.connect("clicked", self.on_reset_clicked)
        hbox.pack_start(button, True, True, 0)

        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textview.connect("key-press-event", self.on_key_pressed)
        self.textview.set_cursor_visible(False)
        vbox.pack_start(self.textview, True, True, 0)
        
        self.load_from_file('ozymandias.txt')

    def load_text(self, text):
        typing_buffer = TypingBuffer()
        typing_buffer.set_text(text)
        typing_buffer.connect("typing-complete",
                              self.on_typing_complete)
        self.textview.set_buffer(typing_buffer)
        self.textview.grab_focus()

    def on_reset_clicked(self, button):
        textbuffer = self.textview.get_buffer()
        start = textbuffer.get_start_iter()
        end = textbuffer.get_end_iter()
        text = textbuffer.get_text(start, end, True)
        self.load_text(text)
    def on_paste_clicked(self, button):
        dialog = PasteDialog(self)
        dialog.run()
        self.load_text(dialog.get_text())
        dialog.destroy()

    def on_load_clicked(self, button):
        dialog = Gtk.FileChooserDialog("Please choose a file", self,
                Gtk.FileChooserAction.OPEN,
                (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                 Gtk.STOCK_OK, Gtk.ResponseType.OK))

        filter_txt = Gtk.FileFilter()
        filter_txt.set_name("Text files")
        filter_txt.add_mime_type("text/plain")
        dialog.add_filter(filter_txt)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.load_from_file(dialog.get_filename())
        dialog.destroy()

    def load_from_file(self, filename):
        try:
            with open(filename, 'r') as f:
                text = f.read()
                self.load_text(text)
        except IOError:
            dialog = Gtk.MessageDialog(self, 0,
                    Gtk.MessageType.ERROR, Gtk.ButtonsType.OK,
                    "Could not open file '{}'.".format(filename))
            dialog.run()
            dialog.destroy()

    def on_key_pressed(self, textview, event):
        return textview.get_buffer().on_key_pressed(event)

    def on_typing_complete(self, textbuffer):
        dialog = ResultsDialog(self, *textbuffer.get_results())
        dialog.run()
        dialog.destroy()

class PasteDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, "Paste text", parent, 0,
                (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                 Gtk.STOCK_OK, Gtk.ResponseType.OK))
        self.set_default_size(150, 100)

        label = Gtk.Label("Paste or type text below:")
        self.textview = Gtk.TextView()

        box = self.get_content_area()
        box.set_orientation(Gtk.Orientation.VERTICAL)
        box.pack_start(label, True, True, 0)
        box.pack_start(self.textview, True, True, 0)
        self.show_all()
        self.textview.grab_focus()

    def get_text(self):
        textbuffer = self.textview.get_buffer()
        start = textbuffer.get_start_iter()
        end = textbuffer.get_end_iter()
        return textbuffer.get_text(start, end, False)

class ResultsDialog(Gtk.Dialog):
    def __init__(self, parent, acc_string, wpm_string, result_strings):
        Gtk.Dialog.__init__(self, "Results", parent, 0,
                (Gtk.STOCK_OK, Gtk.ResponseType.OK))

        buttonbox = self.get_action_area()
        buttons = buttonbox.get_children()
        self.set_focus(buttons[0])
        
        self.set_default_size(500, 300)

        label = Gtk.Label("Typing complete! Here are your results:")

        hbox = Gtk.Box(orientation= Gtk.Orientation.HORIZONTAL, spacing=5)
        hbox.pack_start(Gtk.Label(acc_string), True, True, 0)
        hbox.pack_start(Gtk.Label(wpm_string), True, True, 0)

        flowbox = Gtk.FlowBox()
        flowbox.set_valign(Gtk.Align.START)
        flowbox.set_max_children_per_line(3)
        flowbox.set_selection_mode(Gtk.SelectionMode.NONE)

        self.create_flowbox(flowbox, result_strings)
        

        box = self.get_content_area()
        box.set_orientation(Gtk.Orientation.VERTICAL)
        box.set_spacing(10)

        box.pack_start(label, True, True, 0)
        box.pack_start(hbox, True, True, 0)
        box.pack_start(flowbox, True, True, 0)

        
        self.show_all()

    def create_flowbox(self, flowbox, result_strings):
        for result in result_strings:
            flowbox.add(Gtk.Label(result))
        

class TypingBuffer(Gtk.TextBuffer):
    keys_to_ignore = [Gdk.KEY_Left, Gdk.KEY_Right,
                      Gdk.KEY_Up, Gdk.KEY_Down, Gdk.KEY_Delete]

    __gsignals__ = {
        'typing-complete' : (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, ())
        }
    
    def __init__(self):
        Gtk.TextBuffer.__init__(self)
        self.typed_good = self.create_tag("typed_good",
                                          foreground="white",
                                          background = "green")
        self.typed_bad = self.create_tag("typed_bad",
                                         foreground="white",
                                         background="red")
        self.untyped = self.create_tag("untyped",
                                       foreground="black",
                                       background="white")

        self.last_good = self.create_mark("last_good",
                                          self.get_start_iter(),
                                          True)
        self.last_typed = self.create_mark("last_typed",
                                         self.get_start_iter(),
                                         True)

        self.totals = {}
        self.num_typed_correct = {}
        self.place_cursor(self.get_start_iter())
        self.num_errors = 0
        self.total_errors = 0
        self.started = False
        self.complete = False
        self.start_time = None
        self.end_time = None
        self.last_typed_good = True

    def set_text(self, text):
        Gtk.TextBuffer.set_text(self, text)
        for char in text:
            self.totals[char] = self.totals.get(char, 0) + 1
        self.num_typed_correct = self.totals.copy()

    def on_key_pressed(self, event):
        unichar = Gdk.keyval_to_unicode(event.keyval)

        if event.keyval in TypingBuffer.keys_to_ignore:
            return True

        elif (unichar > 31 or unichar in [8, 9, 10, 13]) and not self.complete:
            if not self.started:
                self.started = True
                self.start_time = time.time()

            char = '\n' if unichar == 13 else chr(unichar)

            insert_iter = self.get_iter_at_mark(self.last_typed)
            next_char = insert_iter.get_char()

            if next_char == char and self.num_errors == 0:
                self.last_typed_good = True
                insert_iter.forward_cursor_position()
                self.move_mark(self.last_good, insert_iter)
                self.move_mark(self.last_typed, insert_iter)
                if (insert_iter.get_offset() 
                        == self.get_end_iter().get_offset()):
                    self.complete = True
                    self.end_time = time.time()
                    self.emit('typing-complete')
                
            elif char == '\u0008':
                if self.num_errors > 0:
                    self.num_errors -= 1
                    insert_iter.backward_cursor_position()
                    self.move_mark(self.last_typed, insert_iter)

            elif not self.complete:
                if self.last_typed_good:
                    self.last_typed_good = False
                    self.num_typed_correct[next_char] -= 1
                    self.total_errors += 1
                insert_iter.forward_cursor_position()
                self.move_mark(self.last_typed, insert_iter)
                self.num_errors += 1

            self.apply_tags()
            return True
        else:
            return False

    def get_results(self):
        results = [(char,
                    self.num_typed_correct[char],
                    self.totals[char])
                   for char in self.totals.keys()]
        results.sort(key = lambda triple : (triple[1] / triple[2], triple[0]))
        whitespace_chars = {' ' : "SPACE", '\n' : "RETURN", '\t' : "TAB"}
        result_strings = []
        for char, correct, total in results:
            char_display = whitespace_chars.get(char, char)
            result_strings.append(
                    "{}: {:.0%} ({}/{})".format(char_display,
                                                correct / total,
                                                correct,
                                                total))

        text = self.get_text(self.get_start_iter(), self.get_end_iter(), False)
        num_words = len(text.split())
        num_chars = len(text)
        chars_correct = num_chars - self.total_errors
        acc_string = "Accuracy: {:.0%} ({}/{})".format(
                chars_correct / num_chars, chars_correct, num_chars)
        wpm_string = "Words per minute: {:.3g}".format(
                num_words * 60 / (self.end_time - self.start_time))
        
        return (acc_string, wpm_string, result_strings)

    def apply_tags(self):
        self.remove_all_tags(self.get_start_iter(), self.get_end_iter())
        self.apply_tag(self.typed_good,
                       self.get_start_iter(),
                       self.get_iter_at_mark(self.last_good))
        self.apply_tag(self.typed_bad,
                       self.get_iter_at_mark(self.last_good),
                       self.get_iter_at_mark(self.last_typed))
        self.apply_tag(self.untyped,
                       self.get_iter_at_mark(self.last_typed),
                       self.get_end_iter())

win =TypingWindow()
win.connect("delete-event", Gtk.main_quit)
win.show_all()
Gtk.main()
