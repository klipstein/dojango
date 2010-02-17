import re

__all__ = ('QueryInfo', 'QueryReadStoreInfo', 
            'JsonRestStoreInfo', 'JsonQueryRestStoreInfo',)

class QueryInfoFeatures(object):
    sorting = True
    paging = False

class QueryInfo(object):
    '''Usage (is that the right solution?):
        info = QueryInfo(request)
        info.extract()
        queryset = extract.process(Object.objects.all())
    '''
    start = 0
    end = 25
    filters = {}
    sorting = [] # key=field // value=descending(True/False)
    
    request = None
    max_count = 25
    
    def __init__(self, request, max_count=None, **kwargs):
        self.request = request
        if max_count is not None:
            self.max_count = max_count

    def extract(self):
        self.set_paging()
        self.set_sorting()
        self.set_filters()
        
    def set_paging(self):
        """Needs to be implemented in a subclass"""
        pass
    
    def set_sorting(self):
        pass
    
    def set_filters(self):
        """Needs to be implemented in a subclass"""
        pass
    
    def process(self, queryset):
        # maybe using Django's paginator
        return queryset.filter(**self.filters).order_by(*self.sorting)[self.start:self.end]

class QueryReadStoreInfo(QueryInfo):
    """
        A helper to evaluate a request from a dojox.data.QueryReadStore 
        and extracting the following information from it:
        
            - paging
            - sorting
            - filters
        
        Parameters could be passed within GET or POST.
    """
    def set_paging(self):
        start = self.request[self.request.method].pop('start', 0)
        # TODO: start = 1???
        count = self.request[self.request.method].pop('count', 25)
        #if not is_number(end): # The dojo combobox may return "Infinity" tsss
        if not is_number(count) or int(count) > self.max_count:
            count = self.max_count
        self.start = int(start)
        self.end = int(start)+int(count)
        
    def set_sorting(self):
        # REQUEST['sort']:
        # value: -sort_field (descending) / sort_field (ascending)
        sort_attr = self.request[self.request.method].pop('sort', None)
        if sort_attr:
            self.sorting.append(sort_attr)
    
    def set_filters(self):
        query_dict = {}
        for k,v in self.request[self.request.method].items():
            query_dict[k] = v

class JsonRestStoreInfo(QueryReadStoreInfo):
    """
        A helper to evaluate a request from a dojox.data.JsonRestStoreInfo
        and extracting the following information:
        
            - paging
            - filters
            
        The paging parameter is passed within the request header "Range".
        Filters are passed via GET (equal to QueryReadStoreInfo).
        
        Sorting is just possible with JsonQueryReadStoreInfo.
    """
    def set_paging(self):
        # Receiving the following header:
        # Range: items=0-24
        # Returning: Content-Range: items 0-24/66
        if 'RANGE' in self.META:
            regexp = re.compile(r"^\s*items=(\d+)-(\d+)", re.I)
            match = regexp.match(self.META['RANGE'])
            if match:
                start, end = match.groups()
                start, end = int(start), int(end)+1 # range-end means including that element!
                self.start = start
                count = self.max_count
                if end-start < self.max_count:
                    count = end-start
                self.end = start+count

    def set_sorting(self):
        # sorting is not available in the normal JsonRestStore
        pass

class JsonQueryRestStoreInfo(QueryInfo):
    jsonpath = None
    jsonpath_filters = None
    jsonpath_sorting = None
    jsonpath_paging = None
    
    def __init__(self, request, **kwargs):
        """
            Matching the following example jsonpath:
            
                /path/[?(@.field1='searchterm*'&@.field2='*search*')][/@['field1'],/@['field2']][0:24]
                
            The last part of the URL will contain a JSONPath-query:
            
                [filter][sort][start:end:step]
        """
        path = request.path
        if not path.endswith("/"):
            path = path + "/"
        # assuming that a least one /path/ will be before the jsonpath query
        # and that the character [ initiates and ] ends the jsonpath
        # [ will be removed from the start and ] from the end
        match = re.match(r'^/.*/(\[.*\])/$', path)
        if match:
            self.jsonpath = match.groups()[0]
        if self.jsonpath:
            # now we remove the starting [ and ending ] and also splitting it via ][
            parts = self.jsonpath[1:-1].split("][")
            for part in parts:
                if part.startswith("?"):
                    self.jsonpath_filters = part
                elif re.match(r'^[/\\].*$', part):
                    self.jsonpath_sorting = part
                # [start:end:step]
                elif re.match(r'^\d*:\d*:{0,1}\d*$', part):
                    self.jsonpath_paging = part
        super(JsonQueryRestStoreInfo, self).__init__(request, **kwargs)
        
    def set_paging(self):
        # handling 0:24
        match = re.match(r'^(\d*):(\d*):{0,1}\d*$', self.jsonpath_paging)
        if match:
            start, end = match.groups()
            if(start.length == 0):
                start = 0
            if(end.length == 0):
                end = int(start) + self.max_count
            start, end = int(start), int(end)+1 # second argument means the element should be included!
            self.start = start
            count = self.max_count
            if end-start < self.max_count:
                count = end-start
            self.end = start+count
    
    def set_sorting(self):
        # handling /@['field1'],/@['field2']
        for f in self.jsonpath_sorting.split(",/"):
            m = re.match(r"([\\/])@\['(.*)'\]", f)
            if m:
                sort_prefix = "-"
                direction, field = m.groups()
                if direction == "/":
                    descending = ""
                self.sorting.append(sort_prefix + field)
        
    def set_filters(self):
        # handling ?(@.field1='searchterm*'&@.field2~'*search*')
        pass 