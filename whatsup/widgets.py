from gi.repository import Gtk


class FeedListWidget(Gtk.ScrolledWindow):
    def __init__(self, feeds):
        super().__init__()
        store = Gtk.ListStore(str, str, int)
        total_unread = sum([f['nt'] for f in feeds.values()])
        store.append(['<all>', 'All', total_unread])
        for k, f in feeds.items():
            title = f['feed_title']
            unread = f['nt']
            if unread == 0:
                continue
            row = [k, title, unread]
            store.append(row)

        view = Gtk.TreeView(store)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Feed", renderer, text=1)
        view.append_column(column)
        column = Gtk.TreeViewColumn("Unread", renderer, text=2)
        view.append_column(column)

        self.tree_view = view
        self.add(view)


class StoriesListWidget(Gtk.TreeView):
    def __init__(self, client):
        store = Gtk.ListStore(str, str)
        super().__init__(store)
        self.store = store
        self.client = client
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Title", renderer, text=0)
        self.append_column(column)

    def on_feed_select_changed(self, selection):
        model, treeiter = selection.get_selected()
        row = model[treeiter]
        feed_id = row[0]
        stories = {'stories': []}
        if feed_id == '<all>':
            stories = self.client.all_stories()
        else:
            stories = self.client.stories(feed_id)
        self.store.clear()
        for story in stories['stories']:
            title = story['story_title']
            content = story['story_content']
            self.store.append([title, content])


class StoryContentWidget(Gtk.TextView):
    def on_story_select_changed(self, selection):
        model, treeiter = selection.get_selected()
        buf = self.get_buffer()
        if treeiter is None:
            buf.set_text('')
        else:
            row = model[treeiter]
            text = row[1]
            buf.set_text(text)


class WhatsupWindow(Gtk.Window):

    def __init__(self, client):
        super().__init__()
        self.client = client

        box = Gtk.Box()

        d = client.feeds()
        wfeeds = FeedListWidget(d['feeds'])
        box.pack_start(wfeeds, True, True, 0)

        vbox = Gtk.Box()
        vbox.set_property('orientation', Gtk.Orientation.VERTICAL)

        wstories = StoriesListWidget(client)
        vbox.pack_start(wstories, True, True, 0)
        wcontent = StoryContentWidget()
        vbox.pack_start(wcontent, True, True, 0)

        box.pack_start(vbox, True, True, 0)

        select = wfeeds.tree_view.get_selection()
        select.connect('changed', wstories.on_feed_select_changed)

        select_story = wstories.get_selection()
        select_story.connect('changed', wcontent.on_story_select_changed)

        self.add(box)
