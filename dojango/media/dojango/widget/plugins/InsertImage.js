dojo.provide("dojango.widget.plugins.InsertImage");

dojo.require("dijit._editor.plugins.LinkDialog");
dojo.require("dojango.widget.ThumbnailPicker");
dojo.declare("dojango.widget.plugins.InsertImage",
	dijit._editor.plugins.LinkDialog,
	{
		// summary:
		//	An editor plugin that uses dojox.image.ThumbailPicker to select an image and inserting it into the editor.
		//	Populates the ThumbnailPicker as the editor attribute "thumbnailPicker", where you can attach your store
		//	via setDataStore. For store examples look at the dojox.image.ThumbnailPicker tests.
		//
		// example:
		// |	// these css files are required:
		// |	// <link rel="stylesheet" href="%{DOJOX_URL}/image/resources/image.css">
		// |	// <link rel="stylesheet" href="%{DOJANGO_URL}/widget/resources/ThumbnailPicker.css">
		// |	dojo.require("dijit.Editor");
		// |	dojo.require("dojango.widget.plugins.InsertImage");
		// |	dojo.require("dojox.data.FlickrRestStore");
		// |	
		// |	var flickrRestStore = new dojox.data.FlickrRestStore();
		// |	var req = {
		// |		query: {
		// |			apikey: "8c6803164dbc395fb7131c9d54843627", tags: ["dojobeer"]
		// |		},
		// |		count: 20
		// |	};
		// |	var editor = new dijit.Editor({}, dojo.place(dojo.body()));
		// |	editor.thumbnailPicker.setDataStore(flickrRestStore, req);
		
		//size, thumbHeight, thumbWidth, isHorizontal <= setting these additional parameters
		command: "insertImage",
		linkDialogTemplate: [
		            '<div id="${id}_thumbPicker" class="thumbPicker" dojoType="dojango.widget.ThumbnailPicker" size="400" isClickable="true"></div>',
		            '<label for="${id}_textInput">${text}</label><input dojoType="dijit.form.ValidationTextBox" required="true" name="textInput" id="${id}_textInput"/>',
		            '<div><button dojoType=dijit.form.Button type="submit">${set}</button></div>'
		        ].join(""),
		_picker: null,
		_textInput: null,
		_initButton: function(){
			this.inherited(arguments);
			this._picker = dijit.byNode(dojo.query("[widgetId]", this.dropDown.domNode)[0]); // creating a unique id should happen outside of initButton
			this._textInput = dijit.byNode(dojo.query("[widgetId]", this.dropDown.domNode)[1]);
			
			dojo.subscribe(this._picker.getClickTopicName(), dojo.hitch(this, "_markSelected"));
			this.dropDown.execute = dojo.hitch(this, "_customSetValue");
			var oldOpen = this.dropDown.onOpen;
			var _this=this;
			this.dropDown.onOpen = function(){
				_this._onOpenDialog();
				dijit.TooltipDialog.prototype.onOpen.apply(this, arguments);
				// resetting scroller (onOpen it is set to 0!)
				var a = _this._picker._thumbs[_this._picker._thumbIndex],
					b = _this._picker.thumbsNode;
				if(typeof(a) != "undefined" && typeof(b) != "undefined" ){
					var left = a.offsetLeft - b.offsetLeft;
					_this._picker.thumbScroller.scrollLeft = left;
				}
			}
			dijit.popup.prepare(this.dropDown.domNode);
			// assigning the picker to the editor
			this.editor.thumbnailPicker = this._picker;
		},
		
		_customSetValue: function(args){
			if(! this._currentItem) {
				return false;
			}
			args.urlInput = this._currentItem['largeUrl'] ? this._currentItem['largeUrl'] : this._currentItem['url'];
			this.setValue(args);
		},
		
		_currentItem: null,
		_markSelected: function(item, idx){
			// url, largeUrl, title, link
			this._currentItem = item;
			if(item.title){
				this._textInput.attr("value", item.title);
			}
			else {
				this._textInput.attr("value", "");
			}
			this._picker.reset();
			dojo.addClass(this._picker._thumbs[item.index], "imgSelected");
		}
	}
);

// Register this plugin.
dojo.subscribe(dijit._scopeName + ".Editor.getPlugin",null,function(o){
	if(o.plugin){ return; }
	switch(o.args.name){
	case "dojangoInsertImage":
		o.plugin = new dojango.widget.plugins.InsertImage({command: "insertImage"});
	}
});