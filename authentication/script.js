// adding lib setting firebase

const firebaseApp = firebase.initializeApp({
    apiKey: "AIzaSyCoLMe-dKO1gneyNr5lF8iij0hUm16n7C8",
  authDomain: "itr-crm-hub.firebaseapp.com",
  projectId: "itr-crm-hub",
  storageBucket: "itr-crm-hub.firebasestorage.app",
  messagingSenderId: "33761625613",
  appId: "1:33761625613:web:239ece62e62b128832f744",
  measurementId: "G-ZT8RH5CD22"
    
    });
   const db = firebaseApp.firestore();
   const auth = firebaseApp.auth();



//    sign-up function
const SignUp=()=>{
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
        console.log(email +"pw- "+ password);
    


    // firebase code
    firebase.auth().createUserWithEmailAndPassword(email, password)
  .then((result) => {
    // Signed in 
    alert("you are signed up , please sign in");
    alert("email= "+ email+" password= "+  password);
    console.log(result);
    window.location.href = "signin.html";
    // ...
  })
  .catch((error) => {
    console.log(error.code);
    console.log(error.message);
    alert(error.message);
    
    
  });


}


// signin function

SignIn=()=>{

     const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    // firebase code
firebase.auth().signInWithEmailAndPassword(email, password)
  .then((result) => {
    // Signed in
    alert("you are  signed in");
   console.log("You are signed in ");
//    window.location.href = "dashboard.html";
    console.log(result);
  })
  .catch((error) => {
    console.log(error.code);
    console.log(error.message);
    alert(error.message);
  });

}