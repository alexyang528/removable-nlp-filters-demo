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


st.sidebar.write("# Configuration")
st.sidebar.write("### Search Experience Info")
EXPERIENCE_KEY = st.sidebar.text_input("Experience Key", value="yext_help_site")
API_KEY = st.sidebar.text_input("API Key", value="1c81e4de0ec0e8051bdf66c31fc26a45")
QUERY = st.sidebar.text_input("Query", value="developer guides")
QUERY = encode_url(QUERY)

UNIVERSAL_URL = f"https://liveapi.yext.com/v2/accounts/me/answers/query?experienceKey={EXPERIENCE_KEY}&api_key={API_KEY}&v=20190101&version=STAGING&locale=en&input={QUERY}"
response = get_results(UNIVERSAL_URL)
vertical_keys = [r["verticalConfigId"] for r in response["response"]["modules"]]


def write_vertical(vertical_key):
    st.write(f"# {vertical_key}")

    vertical_url = f"https://liveapi.yext.com/v2/accounts/me/answers/vertical/query?experienceKey={EXPERIENCE_KEY}&api_key={API_KEY}&v=20190101&version=STAGING&locale=en&input={QUERY}&verticalKey={vertical_key}"

    response = get_results(vertical_url)
    results = response["response"]["results"]
    filters = response["response"]["appliedQueryFilters"]

    filters_selected = st.multiselect(
        f"Filters ({vertical_key})",
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

        final_url = vertical_url + f"&facetFilters={{{facet_filters}}}"
    else:
        final_url = vertical_url

    final_response = get_results(final_url)
    final_results = final_response["response"]["results"]
    result_count = final_response["response"]["resultsCount"]

    if len(final_results) == 0:
        st.write("_No results returned._")
    else:
        if len(final_results) > 5:
            final_results = final_results[:5]

        st.write(f"Results Count: {result_count}")

        display_fields = st.sidebar.multiselect(
            f"Display Fields ({vertical_key})", final_results[0]["data"].keys()
        )
        for result in final_results:
            st.write(f"## {result['data']['name']}")
            for field in display_fields:
                if field in result["data"]:
                    st.write(f"**{field}**: {result['data'][field]}")
                else:
                    st.write(f"**{field}**: _None_")
            st.markdown("""---""")

        with st.expander("API Request"):
            st.code(final_url, language="html")

        with st.expander("API Response"):
            st.write(response)


st.sidebar.write("### Display Fields:")
for vertical_key in vertical_keys:
    write_vertical(vertical_key)
