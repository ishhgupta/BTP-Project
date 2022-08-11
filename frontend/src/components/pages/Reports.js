import React, { useEffect } from "react";
import { Controller, useForm } from "react-hook-form";
import Button from "@mui/material/Button";
import CssBaseline from "@mui/material/CssBaseline";
import TextField from "@mui/material/TextField";
import FormControlLabel from "@mui/material/FormControlLabel";
import Checkbox from "@mui/material/Checkbox";
import Link from "@mui/material/Link";
import Grid from "@mui/material/Grid";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Container from "@mui/material/Container";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import Context from "@mui/base/TabsUnstyled/TabsContext";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import axios from "axios";
import { Card } from "@mui/material";
import List from "./List"
export const theme = createTheme();

export default function Reports() {
  const [user, setUser] = React.useState([]);
//   useEffect(() => {
//     if (!localStorage.getItem("user")) window.location.href = "/";
//     const user = JSON.parse(localStorage.getItem("user"));
//     if (user.usertype !== 2) window.location.href = "/";
//     setUser(user);
//     console.log("user")
//     console.log(user);
//   }, []);

  return (
    <ThemeProvider theme={theme}>
      <Container component="main" maxWidth="xs">
        <CssBaseline />
       
        <Box
            sx={{
            marginTop: 8,
            display: "flex",
            flexDirection: "row",
            }}
        >
        <TestList />
      </Box>
      </Container>
      
    </ThemeProvider>
  );
}

export function TestList() {
  const [tests, setTests] = React.useState([]);
  const [inputText, setInputText] = React.useState("");
  useEffect(() => {
    // console.log("token", localStorage.getItem("access_token"));
    axios
      .get("http://localhost:5000/allTests", {
        // headers: {
        //   Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        // },
      })
      .then((res) => {
        // console.log("tests", res.data);
        // console.log("tests", tests);
        setTests(res.data.tests);
        console.log(tests);
        // convert string to array of objects
      })
      .catch((err) => {
        console.log(err);
      });
  }, []);

  let inputHandler = (e) => {
    //convert input text to lower case
    var lowerCase = e.target.value.toLowerCase();
    setInputText(lowerCase);
  };

  return (
    <Container component="main" maxWidth="sm">
    <TextField
          id="outlined-basic"
          onChange={inputHandler}
          variant="outlined"
          fullWidth
          label="Search"
        />
      <List tests={tests} input={inputText} />
      {/* <div> */}
      {/* {tests.map((test) => (
        <TestCard key={test.id} test={test} />
      ))} */}
    </Container>
    // </div>
  );
}

const TestCard = ({ test }) => {
  console.log(test);
  return (
    <Card
      sx={{
        marginTop: 8,
        display: "flex",
        flexDirection: "row",
      }}
      onClick={() => (window.location.href = `/test/${test.id}`)}
    >
      {/* <Grid> */}
      <Grid item xs={8}>
        <Typography variant="h5" component="h2">
          {test.case_number}
        </Typography>
      </Grid>
      <Grid item xs={8}>
        <Typography variant="body2" component="p">
          {test.case_name}
        </Typography>
      </Grid>
      <Grid item xs={8}>
        <Typography variant="body2" component="p">
          {test.date}
        </Typography>
      </Grid>
    </Card>
    // </Grid>
  );
};
