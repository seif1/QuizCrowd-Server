const quiz = {
    quizName: "",
    quizDescription: "",
    questions: {}
}

function print_json() {
    console.clear()
    console.log(quiz)
}

// Adding event listeners to the quiz description to update the json object when the item changes
const quizname = document.getElementById("quizName")
quizname.addEventListener("input", (event) => {
    quiz[event.target.id] = event.target.value
    print_json()
})

// Adding event listeners to the quiz description to update the json object when the item changes
const quizdescription = document.getElementById("quizDescription")
quizdescription.addEventListener("input", (event) => {
    quiz[event.target.id] = event.target.value
    print_json()
})

// A dictionary between the internal question types, and more easily displayed versions
const dictionary = {
    "multiChoice": "Multiple Choice",
    "checkBox": "Check Box"
}

// This function ensures the question numbers are correct
function fix_question_numbers() {
    list = document.getElementById("question_list")
    i = 1
    for (node of list.children) {
        node.querySelector("#"+node.id+"_name").innerText = "Question #"+i
        i++
    }
}

// This function handles safely deleting new question
function delete_question(node, questionID) {
    // Remove question from json
    delete quiz["questions"]["questionID_"+questionID]
    // Remove question from DOM
    node.parentNode.parentNode.remove()
    
    fix_question_numbers()
}

function delete_answer(node, question_ID, answer_ID) {
    // Remove question from json
    delete quiz["questions"]["questionID_"+question_ID]["answers"]["answerID_"+answer_ID]
    // Remove question from DOM
    node.parentNode.remove()
}

// This function handles adding new questions
function add_question(type) {
    // Find the question type, duplicate it, and set up neccesary values
    template = document.getElementById("question_template")
    
    clone = template.content.cloneNode(true)

    unique_ID = Math.floor(Math.random()*10000)

    // This ensures the question ID is unique (a requirement for HTML)
    while(document.getElementById("question_list").querySelector("#questionID_"+unique_ID) != null) {
        unique_ID = Math.floor(Math.random()*10000)
    }

    // Set template values for later reference
    // Main question ID
    clone.getElementById("template_id").id = "questionID_"+unique_ID

    // Top Right Identifier of question type
    clone.getElementById("question_type").innerText = dictionary[type]
    clone.getElementById("question_type").id = "question_type_"+unique_ID

    // Question Delete Button
    clone.getElementById("delete_question_button").setAttribute("onclick", 'delete_question(this, "'+unique_ID+'")')
    clone.getElementById("delete_question_button").id = "delete_question_button_"+unique_ID

    // Question Name field
    clone.getElementById("question_name").id = "questionID_"+unique_ID+"_name"

    // Text Label
    clone.getElementById("text_label").setAttribute("for", "text_label_area_"+unique_ID)
    //.for = "text_label_area_"+unique_ID
    clone.getElementById("text_label").id = "text_label_"+unique_ID

    // Add a question into the object with the key of its unique_ID
    quiz["questions"]["questionID_"+unique_ID] = {
        "question_text": "",
        "type": typeDictionary[type],
        "answers": {}
    }

    // Text Area
    clone.getElementById("text_label_area").name = "text_label_area_"+unique_ID
    clone.getElementById("text_label_area").addEventListener("input", (event) => {
        // Updates the question JSON
        quiz["questions"][event.target.parentNode.id]["question_text"] = event.target.value
    })
    clone.getElementById("text_label_area").id = "text_label_area_"+unique_ID

    // Button Values
    clone.getElementById("add_answer_button").setAttribute("onclick", 'add_answer("'+unique_ID+'","'+type+'")')
    clone.getElementById("add_answer_button").id = "add_answer_button_"+unique_ID

    clone.getElementById("answer_list").id = "answer_list_"+unique_ID

    // Add question into question list
    document.getElementById("question_list").appendChild(clone)

    fix_question_numbers()
}

const typeDictionary = {
    "multiChoice": "radio",
    "checkBox": "checkbox"
}

function add_answer(questionID, type) {
    template = document.getElementById("answer_template")
    clone = template.content.cloneNode(true)

    answer_ID = Math.floor(Math.random()*10000)
    // This ensures the question ID is unique (a requirement for HTML)
    while(document.getElementById("question_list").querySelector("#answerID_"+answer_ID) != null) {
        answer_ID = Math.floor(Math.random()*10000)
    }

    // Lable clone template correctly
    clone.getElementById("answer_id").id = "answerID_"+answer_ID

    // Create the "blank" answer format
    quiz["questions"]["questionID_"+questionID]["answers"]["answerID_"+answer_ID] = {
        "answerText": "",
        "answer": false,
    }

    // Answer radio/checkbox modifications
    clone.getElementById("answer_value").type = typeDictionary[type]
    clone.getElementById("answer_value").name = "answer_value_"+questionID
    if (typeDictionary[type] == "radio") {
        clone.getElementById("answer_value").addEventListener("input", (event) => {
            // Set all the "answer" fields to false to mimick the behavior of the radio input
            for (item in quiz["questions"][event.target.parentNode.parentNode.parentNode.id]["answers"]) {
                quiz["questions"][event.target.parentNode.parentNode.parentNode.id]["answers"][item]["answer"] = false
            }

            // Set the answer we just selected to the "true" value internally
            quiz["questions"]["questionID_"+questionID]["answers"][event.target.parentNode.id]["answer"] = event.target.checked
        })
    } else if (typeDictionary[type] == "checkbox") {
        clone.getElementById("answer_value").addEventListener("input", (event) => {
            // Update the internal value to mimick the changed checkbox
            quiz["questions"][event.target.parentNode.parentNode.parentNode.id]["answers"][event.target.parentNode.id]["answer"] = event.target.checked
        })
    }
    clone.getElementById("answer_value").id = "answer_value_"+answer_ID

    // update the text and setup listener so that we can update internal values correctly
    clone.getElementById("answer_text")
    clone.getElementById("answer_text").name = "answer_text_"+questionID
    clone.getElementById("answer_text").addEventListener("input", (event) => {
        quiz["questions"][event.target.parentNode.parentNode.parentNode.id]["answers"][event.target.parentNode.id]["answerText"] = event.target.value
    })
    clone.getElementById("answer_text").id = "answer_text_"+answer_ID

    // Answer Delete Button
    clone.getElementById("delete_answer_button").setAttribute("onclick", 'delete_answer(this, "'+questionID+'",  "'+answer_ID+'")')
    clone.getElementById("delete_answer_button").id = "delete_answer_button_"+answer_ID

    // Add modified template copy to answer list
    document.getElementById("answer_list_"+questionID).appendChild(clone)
}

// Handles the submit event
function handleSubmit(event) {
    event.preventDefault();

    fetch('/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(quiz)
      }).then(response => {
        // This acts as a html redirect (no ability to go back)
        //window.location.replace(response.url);

        // This acts as a user click on link (can go back)
        window.location.href = response.url
      })

      return;
}

// Creates the submit listener, and hooks it to the handleSubmit function.
const form = document.querySelector("form");
form.addEventListener("submit", handleSubmit);