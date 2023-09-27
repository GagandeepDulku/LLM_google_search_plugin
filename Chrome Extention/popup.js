document.addEventListener("DOMContentLoaded", function() {

  chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
    const clickMeButton = document.getElementById("ask_btn");
    const inputTextArea = document.getElementById("query");

    clickMeButton.addEventListener("click", function() {
      var text = inputTextArea.value;
      var sliderValue = document.querySelector('input[type="checkbox"]').checked;
      var url = tabs[0].url;

      document.getElementById("response").textContent = "Waiting for response"

      if(isTextNotEmpty(text)){
        var api_url = "http://127.0.0.1:5000/query";
        var final_url = `${api_url}?query=${text}`;
      }else if(validateQueryLink(url)){
        if(!sliderValue){
          query = extractLink(url)
          var api_url = "http://127.0.0.1:5000/query";
          var final_url = `${api_url}?query=${query}`;
        }
        else{
          var api_url = "http://127.0.0.1:5000/serp";
          const encodedUrl = encodeURIComponent(url);
          var final_url = `${api_url}?url=${encodedUrl}`;
        }  
      }else{
        document.getElementById("waitingText").style.display = "none";
        document.getElementById("output").style.display = "block";
        document.getElementById("response").textContent = "This Webpage is not google search page and no text in the query prompt text field";
      }

      console.log("Text from textarea:", text);
      console.log("valid sentence as Query",validateSentence(text))
      console.log("Use Google:", sliderValue);



      fetch(final_url)
            .then(response => response.json())
            .then(data => {
              console.log(data);
              document.getElementById("output").style.display = "block";
              document.getElementById("response").textContent = cleanString(removeNewlines(data.output));
            })
            .catch(error => {
              console.error("Error:", error);
              document.getElementById("output").style.display = "block";
              document.getElementById("response").textContent = "Error occurred while making the request.";
            });


    });
  });
});

function removeNewlines(inputString) {
  return inputString.replace(/\n/g, "");
}


function cleanString(inputString) {
  // // Replace non-alphanumeric characters with spaces
  // const cleanedString = inputString.replace(/[^a-zA-Z0-9 ]/g, " ");
  
  // Remove extra spaces and trim
  const finalString = inputString.replace(/\s+/g, " ").trim();
  
  return finalString;
}

function isTextNotEmpty(text) {
  const cleanedText = text.replace(/[^a-zA-Z0-9]/g, ""); // Remove non-alphanumeric characters
  return cleanedText.length > 0;
}

function validateSentence(text) {
  // Basic sentence validation criteria (you can modify this as needed)
  const sentencePattern = /^[A-Z][^.!?]*[.!?]$/;
  return sentencePattern.test(text);
}

function validateQueryLink(url) {
  const ql = "" + url;
  const pattern = /q=(.*?)&rlz/; // 'q=' Query + Words '&rlz'
  const match = ql.match(pattern);
  
  if (match) {
    return true;
  } else {
    console.log("Query could not have been found in the provided link using known format, please check link and matching regex");
    return false;
  }
}

function extractLink(url) {
  const ql = "" + url;
  const pattern = /q=(.*?)&rlz/; // 'q=' Query + Words '&rlz'
  const match = ql.match(pattern);
  return match[1].replace(/\+/g, " ");
}
