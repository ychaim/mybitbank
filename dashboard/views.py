import config
import generic
import calendar
import urllib2
from connections import connector
from events.models import Events
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    '''
    Handler for the dashboard main page
    '''
    currect_section = 'dashboard'
    
    # get all wallets
    wallets = generic.getWallets(connector)

    # more efficient if we do only one call
    transactions = []
    for wallet in wallets:
        transactions = transactions + wallet.getTransactions(5, 0)
    
    # sort result
    transactions = sorted(transactions, key=lambda k: k.get('time',0), reverse=True)
    
    # get only 10 transactions
    transactions = transactions[0:10]

    # events
    list_of_events = Events.objects.all().order_by('-entered')[:10]  
    for single_event in list_of_events:
        timestamp = calendar.timegm(single_event.entered.timetuple())
        single_event.entered_pretty = generic.twitterizeDate(timestamp)
    
    page_title = "Dashboard"
    sections = generic.getSiteSections('dashboard')
    context = {
               'globals': config.MainConfig['globals'], 
               'system_errors': connector.errors,
               'system_alerts': connector.alerts,
               'request': request,
               'breadcrumbs': generic.buildBreadcrumbs(currect_section), 
               'page_title': page_title, 
               'page_sections': sections, 
               'wallets': wallets, 
               'transactions': transactions,
               'events': list_of_events
               }
    return render(request, 'dashboard/index.html', context)

@login_required
@csrf_exempt
def proxy(request):
    '''
    Proxy script view for rates ticker APIs
    '''
    
    if request.is_ajax():
        if request.method == 'POST':
            url = request.body
            cache_hash = connector.getParamHash(url)
            cache_object = connector.cache.fetch('rates', cache_hash)
            if cache_object:
                return HttpResponse(cache_object, content_type="application/json")
            else:
                opener = urllib2.build_opener()
                opener.addheaders = [('User-agent', "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:25.0) Gecko/20100101 Firefox/25.0")]
                response = opener.open(url)
                rates_json = response.read()
                connector.cache.store('rates', cache_hash, rates_json, 60)
                return HttpResponse(rates_json, content_type="application/json")
