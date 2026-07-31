# Implement `gocolly/colly`

You are given a Go repository at `/testbed`, reset to a skeleton commit: every function body has been replaced with a stub that panics on call.

You need to complete the implementations for all functions and pass the unit tests.
Do not change the names of existing functions, types, or methods, as they may be referenced from other code like unit tests, etc.
When you generate code, you must maintain the original formatting of the original function stubs (such as whitespaces), otherwise we will not be able to search/replace blocks for code modifications, and therefore you will receive a score of 0 for your generated code.

## Repository details

- Upstream project: `gocolly/colly`
- Source directory to implement: `./`
- Test command: `go test -json -count=1 ./...` (run against `.`)
- Specification / docs: https://pkg.go.dev/github.com/gocolly/colly/v2

Implement only the library source under the source directory. Do not modify the test files.

>>> Here is the Specification Information:

Lightning Fast and Elegant Scraping Framework for Gophers Colly provides a clean interface to write any kind of crawler/scraper/spider.

With Colly you can easily extract structured data from websites, which can be used for a wide range of applications, like data mining, data processing or archiving.

backers backers 8 sponsors sponsors 11 11 CI CI passing passing report card a+ learn by examples coverage coverage 54% 54% twitter twitter follow follow Clean API Fast (>1k request/sec on a single core) Manages request delays and maximum concurrency per domain Automatic cookie and session handling Sync/async/parallel scraping Caching Automatic encoding of non-unicode responses Robots.txt support Distributed scraping Configuration via environment variables Extensions Colly Features Example import ( "fmt" "github.com/gocolly/colly/v2" ) func main() { c := colly.NewCollector() // Find and visit all links c.OnHTML("a[href]", func(e *colly.HTMLElement) { e.Request.Visit(e.Attr("href")) }) c.OnRequest(func(r *colly.Request) { fmt.Println("Visiting", r.URL) }) See examples folder for more detailed examples.

go get github.com/gocolly/colly/v2 Bugs or suggestions? Visit the issue tracker or join #colly on freenode Below is a list of public, open source projects that use Colly: greenpeace/check-my-pages Scraping script to test the Spanish Greenpeace web archive.

altsab/gowap Wappalyzer implementation in Go.

jesuiscamille/goquotes A quotes scraper, making your day a little better!

jivesearch/jivesearch A search engine that doesn't track you.

Leagify/colly-draft-prospects A scraper for future NFL Draft prospects.

lucasepe/go-ps4 Search playstation store for your favorite PS4 games using the command line.

yringler/inside-chassidus-scraper Scrapes Rabbi Paltiel's web site for lesson metadata.

gamedb/gamedb A database of Steam games.

lawzava/scrape CLI for email scraping from any website.

eureka101v/WeiboSpiderGo A sina weibo(chinese twitter) scraper Go-phie/gophie Search, Download and Stream movies from your terminal imthaghost/goclone Clone websites to your computer within seconds.

superiss/spidy Crawl the web and collect expired domains.

docker-slim/docker-slim Optimize your Docker containers to make them smaller and better.

seversky/gachifinder an agent for asynchronous scraping, parsing and writing to some storages(elasticsearch for now) eval-exec/goodreads crawl all tags and all pages of quotes from goodreads.

If you are using Colly in a project please send a pull request to add it to the list.

c.Visit("http://go-colly.org/") } Installation Bugs Other Projects Using Colly This project exists thanks to all the people who contribute. [Contribute].

Thank you to all our backers! 🙏 [Become a backer] Support this project by becoming a sponsor. Your logo will show up here with a link to your website. [Become a sponsor]

colly@20d31482af5f754832a753f88517f No issues found • 4 Obligations from 8 Licenses • 19 Dependencies View details on FOSSA Contributors Backers Sponsors License
