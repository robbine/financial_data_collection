from celery import shared_task
from .crawl_tasks import _execute_crawl_task
from .crawl_tasks import CrawlConfig

@shared_task(queue='sec_edgar_queue')
def crawl_edgar_filings(cik: str, form_type: str = '10-K'):
    config = CrawlConfig(
        url=f'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={form_type}&dateb=&owner=include&count=10&search_text=',
        headers={
            'User-Agent': 'Mozilla/5.0 (compatible; FinancialDataCollector/1.0; contact@example.com)'
        },
        parser='edgar_listing',
        params={'cik': cik, 'form_type': form_type}
    )
    return _execute_crawl_task(config)
