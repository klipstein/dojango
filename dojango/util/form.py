from dojango.util import is_number

def get_combobox_data(request):
    """Return the standard live search data that are posted from a ComboBox widget.
    summary:
        A ComboBox using the QueryReadStore sends the following data:
            name - is the search string (it always ends with a '*', that is how the dojo.data API defined it)
            start - the paging start
            count - the number of entries to return
        The ComboBox and QueryReadStore usage should be like this:
            <div dojoType="dojox.data.QueryReadStore" jsId="topicStore" url="/topic/live-search/..." requestMethod="post" doClientPaging="false"></div>
            <input {% dojo_widget "rs.widget.Tagcombobox" "addTopicInput" %} store="topicStore" style="width:150px" pageSize="20" />
        The most important things here are the attributes requestMethod and doClientPaging!
        The 'doClientPaging' makes the combobox send 'start' and 'count' parameters and the server
        shall do the paging.
        
    returns:
        a tuple containing
            search_string - the string typed into the combobox
            start - at which data set to start
            end - at which data set to stop
        'start' and 'end' are already prepared to be directly used in the 
        limit part of the queryset, i.e. Idea.objects.all()[start:end]
    
    throws:
        Exception - if the request method is not POST.
        ValueError - if start or count parameter is not an int.
    """
    if not request.method=='POST':
        raise Exception('POST request expected.')
    string = request.POST.get('name', '')
    if string.endswith('*'): # Actually always the case.
        string = string[:-1]
    start = int(request.POST.get('start', 0))
    end = request.POST.get('count', 10)
    if not is_number(end): # The dojo combobox may return "Infinity" tsss
        end = 10
    end = start+int(end)
    return string, start, end