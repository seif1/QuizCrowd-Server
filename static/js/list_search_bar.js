const search_text = document.getElementById("search_text")
const search_by = document.getElementById("search_by")
const list_area = document.getElementById("quiz_list")

search_text.addEventListener("input", (event) => {
    new_search = event.target.value
    update_search(new_search)
})

search_by.addEventListener("input", (event) => {
    new_search = search_text.value
    update_search(new_search)
})

function update_search(new_search) {
    if(new_search != '') {
        for(item of list_area.children) {
            search_param = item.getAttribute(search_by.value)

            if (search_param.includes(search_text.value)) {
                item.hidden = false
            } else {
                item.hidden = true
            }
        }
    } 
    else {
        for(item of list_area.children) {
            item.hidden = false
        }
    }
}