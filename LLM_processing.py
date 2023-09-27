import requests
from bs4 import BeautifulSoup
import re

from langchain.document_loaders import WebBaseLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI
from serpapi import GoogleSearch

import openai
import os
openai.api_key = os.environ["OPENAI_API_KEY"]
SERPkey = ""




# SERP API MTHODS
def get_search_dict(query, serp_key = SERPkey):

    """
    get the google search result in the form of dictionary

    @Params
        query    : query that needs to be googled
        serp_key : API key for authentication

    @Return
        Dictionary conataining the google search results
    """
    search = GoogleSearch({
            "q": query, 
            "api_key": SERPkey
        })

    return search.get_dict()

def get_organic_links(query, top_limit = 5):

    """
    get the top results link for the given query

    @Params
        query : query that needs to be googled
        top_limit : limit of top results that need to be fetched
    @Return
        a list containg links of organic search results
    """
    ret_list = []
    search_dict = get_search_dict(query, SERPkey)
    for oi, ors in enumerate(search_dict["organic_results"]):
        if oi < top_limit:
            ret_list.append(ors["link"])

    return ret_list

def get_news_page(query):

    """
        It returns the news tab page link for the given query on google search

        @Params
            query : query that needs to be googled
        @Return
            a link of the news tab page for the query result

    """

    search_dict = get_search_dict(query)

    menu_items = search_dict["search_information"]["menu_items"]
    news_link = ""
    for it in menu_items:
        if it["title"] == "News":
            news_link = it["link"]
    if news_link == "":
        print("No news link")
    else:
        return news_link

# GOOGLE SEARCH URL EXTRACTION METHODS


def check_exluded(url):
    exclude_list = ["www.youtube.com"]
    for ex in exclude_list:
        if ex in url:
            return True
        
    return False

def extract_links(query_search_link):

    """
    It extracts all the links on the google search page using the link of the query page

    @Params
        query_search_link =  The URL for the given query search result
    @ Retruns
          A list of links return in the google search 
    """

    ret_list = []
    exclude_list = ["www.youtube.com"]
    soup = BeautifulSoup(requests.get(query_search_link).content, features="lxml")
    for a in soup.find_all("a"):
        link = a.attrs["href"]
        pattern = r'/url\?q=(.*?)&sa='
        match = re.search(pattern, link)
        if match:
            if not check_exluded(match[1]):
                ret_list.append(match[1])
            else:
                print("The extracted URL is present in exlude list : ", match[1])
    return ret_list[:-2]


def extract_query_from_link(url):

    """
    Extract query as a sentence from the URL of the query result

    @Params
        url = Query URL of goolge search results
    @Returns
        string of query as a sentence, it returns None if query wasn't found

    """
    ql = ""+url
    pattern = r'q=(.*?)&rlz' # 'q=' Query + Words '&rlz'
    match = re.search(pattern, ql)
    if match:
        return match[1].replace("+", " ")
    else:
        print("Query could not have been found in the provided link using known format, please check link and matching regex")


    

    
def get_refined_links(link):

    """
    This method is used to extract all the links from the news tab page of the google search results
    @Params
        link : Link to the news tab page of googe search results
    @Return
        a list containg all the links on the news page 
    """
    ret_list = []
    soup = BeautifulSoup(requests.get(link).content, features="lxml")
    all_links = soup.find_all("a", href = re.compile("(?<=/url\?q=)(htt.*://.*)"))
    for al in all_links:
        if "data-ved" in al.attrs.keys():
            ret_list.append(al.attrs["href"].replace("/url?q=",""))
    return ret_list


# LLM METHOD

def get_llm_response_from_links(query, link_list):

    """
        This method use the LLM, and a list of links to answere the given query

        @Params
            query : Query as a text string that needs to be answered 
            link_list : List of links that need to be processed and supposingly contains the answer

        @Return
            A dictionary containg the output response of the LLM used in the method 
    
    """
    
    # Extract data
    data = []
    for link_e in link_list:
        loader = WebBaseLoader(link_e)
        try:
            data.append(loader.load()[0])
        except requests.exceptions.RequestException as e:
            print("Error occured while loading this url : ", link_e)
            print("Error:", e)

    # split data into chunks
    char_splitter = CharacterTextSplitter(
                        chunk_size    = 200,
                        chunk_overlap = 0,
                        separator=  "\n"
                    )
    split_text  = char_splitter.split_documents(data)
    split_text, _ = refine_meta_data(split_text)
    
    # Embeddingings
    oai_embeding = OpenAIEmbeddings()

    # Creating Vector Embedding from the spliited chunks of the webpage
    doc_search = Chroma.from_documents( split_text,
                                        oai_embeding)

    # Creating reteiver object to retrieve vectors relevant to the query 
    retriever = doc_search.as_retriever(search_type = "mmr")
    docs   = retriever.get_relevant_documents(query)

    chain  = load_qa_chain(OpenAI(temperature = 0), chain_type = "stuff") 
    output = chain({"input_documents":docs, "question":query}, return_only_outputs=False)

    return output


def get_response_from_query(query):

    """
        This method takes a prompt as a query and generate LLM repsonse using only that query text, No links or extra documents (for fast response)

        @Params
            query : Query as a text string that needs to be answered
        @Return
            A dictionary containg the output response of the LLM used in the method
    """

    chain  = load_qa_chain(OpenAI(temperature = 0), chain_type = "stuff") 
    return chain({"input_documents":[], "question":query}, return_only_outputs=True)

# HELPER METHOD

def refine_meta_data(split_text):

    """
    This method is used to clean the splitted meta data,
    if the meta data dictionary of a chunk contains a None value the vectorization process fails, 
    this method rectifies that scenario by converting the object into exceptable format i.e string
    
    @Params
        split_text : documents splitted into chunks object
    @Return
        the same object with rectified meta data if required.
        list containg the incex of the chunks that needed to be rectified (for debugging purpose)

    """

    ret_list = []
    for si, s in enumerate(split_text):
        for key in s.metadata.keys():
            if not isinstance(s.metadata[key], str):
                str_val = str(s.metadata[key])
                s.metadata[key] = str_val
                split_text[si].metadata = s.metadata
                print("Updating meta data of split index "+str(si)+"-"+key+"-"+str_val)
                ret_list.append(si)
            
    return split_text, ret_list


def validate_search_url(url):
    """ it validates if the url belongs to a google search or not, return true if it google search URL """
    return url.startswith("https://www.google.com/search?q=")


def get_response_from_URL(query_search_link):
    # Extract query
    query = extract_query_from_link(query_search_link)

    # Extract links
    if query:
        link_list = extract_links(query_search_link)
    # Get LLMs response
        if len(link_list) > 0:
            response = get_llm_response_from_links(query, link_list)
            return response
        else:
            {"flag": False}
            print("No links could have been extracted from the URL")
    else:
        print("Query could not have extracted from given URL")


