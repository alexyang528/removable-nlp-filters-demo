import requests
import streamlit as st
from urllib.parse import quote_plus as encode_url

st.set_page_config(page_title="Removable NLP Filters Demo", layout="wide")


def flatten(values):
    out = []
    for value in values:
        if isinstance(value, list):
            out.extend(flatten(value))
        else:
            out.append(value)
    return out


@st.experimental_memo(ttl=600)
def get_results(URL):
    return requests.get(URL).json()


st.sidebar.write("# Search Experience Info")
experience_key = st.sidebar.text_input("Experience Key", value="yext_help_site")
api_key = st.sidebar.text_input("API Key", value="1c81e4de0ec0e8051bdf66c31fc26a45")
vertical_key = st.sidebar.text_input("Vertical Key", value="guides")
query = st.sidebar.text_input("Query", value="API guides")
query = encode_url(query)

URL = f"https://liveapi.yext.com/v2/accounts/me/answers/vertical/query?experienceKey={experience_key}&api_key={api_key}&v=20190101&version=STAGING&locale=en&input={query}&verticalKey={vertical_key}"

response = get_results(URL)
results = response["response"]["results"]

if len(results) == 0:
    st.write("_No results returned._")
else:
    if len(results) > 10:
        results = results[:10]

    filters = response["response"]["appliedQueryFilters"]
    display_fields = st.sidebar.multiselect("Display Fields", results[0]["data"].keys())

    st.write(f"# {vertical_key}")

    filters_selected = st.multiselect(
        "",
        [f"{filter['displayKey']}: {filter['displayValue']}" for filter in filters],
        default=[f"{filter['displayKey']}: {filter['displayValue']}" for filter in filters],
    )
    corresponding_filters = [
        filter
        for filter in filters
        if f"{filter['displayKey']}: {filter['displayValue']}" in filters_selected
    ]

    if corresponding_filters != filters:

        removed_filters = [filter for filter in filters if filter not in corresponding_filters]
        removed_filter_keys = [list(filter["filter"].keys()) for filter in removed_filters]
        removed_filter_keys = flatten(removed_filter_keys)
        removed_filter_keys = [k for k in removed_filter_keys if k != "type"]
        facet_filters = ",".join([f'"{key}": []' for key in removed_filter_keys])

        final_url = URL + f"&facetFilters={{{facet_filters}}}"
    else:
        final_url = URL

    final_response = get_results(final_url)
    final_results = final_response["response"]["results"]
    result_count = final_response["response"]["resultsCount"]

    st.write(f"Results Count: {result_count}")

    for result in final_results:
        st.write(f"## {result['data']['name']}")
        for field in display_fields:
            if field in result["data"]:
                st.write(f"**{field}**: {result['data'][field]}")
            else:
                st.write(f"**{field}**: _None_")
        st.markdown("""---""")

    with st.expander("API Request"):
        st.write(final_url)

    with st.expander("API Response"):
        st.write(response)
