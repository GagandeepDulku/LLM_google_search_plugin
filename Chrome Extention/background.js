// chrome.action.onClicked.addListener(function() {
//   chrome.scripting.executeScript({
//     target: { tabId: 0 },
//     function: () => {
//       chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
//         const activeTab = tabs[0]; // Get the first (and only) tab in the array
//         const activeTabUrl = activeTab.url; // Extract the URL from the tab object
//         alert(activeTabUrl);
//       });
//     }
//   });
// });


// // chrome.action.onClicked.addListener(function() {
// //   chrome.scripting.executeScript({
// //     target: { tabId: 0 },
// //     function: () => {
// //       chrome.tabs.query({}, function(tabs) {
// //         const urls = tabs.map(tab => tab.url);
// //         alert(urls.join('\n'));
// //       });
// //     }
// //   });
// // });
