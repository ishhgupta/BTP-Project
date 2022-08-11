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
export const theme = createTheme();

function List(props) {
  const filteredData = props.tests.filter((el) => {
    if (props.input === "") {
      return el;
    } else {
      return el.case_number.toLowerCase().includes(props.input);
    }
  });
  return (
    <ul>
      {filteredData.map((test) => (
        <TestCard key={test.id} test={test} />
      ))}
    </ul>
  );
}

const TestCard = ({ test }) => {
  function downloadpdf() {
    fetch("www.google.com", {
      method: "GET",
      headers: {
        "Content-Type": "html",
      },
    })
      .then((response) => response.blob())
      .then((blob) => {
        // Create blob link to download
        const url = window.URL.createObjectURL(new Blob([blob]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", `FileName.pdf`);

        // Append to html link element page
        document.body.appendChild(link);

        // Start download
        link.click();

        // Clean up and remove the link
        link.parentNode.removeChild(link);
      });
  }

  // var wkhtmltopdf = require('wkhtmltopdf');
  function plsPrint(id){
    let windowP =  window.open(`/test/${id}`);
   windowP.open();
    windowP.onload = function(){
    console.log(id);
    // document.title='My new title';
    windowP.print();
    windowP.onafterprint=function(){ windowP.close();}
}
    }
  console.log(test);
  return (
    <Card
      sx={{
        marginTop: 8,
        display: "flex",
        flexDirection: "row",
      }}
            // onClick={() => (window.location.href = `/test/${test.id}`)}
    >
      <Grid item xs={6}>
        <Typography variant="h5" component="h2">
          {test.case_number}
        </Typography>
      </Grid>
      <Grid item xs={6}>
        <Typography variant="body2" component="p">
          {test.case_name}
        </Typography>
      </Grid>
      <Grid item xs={6}>
        <Typography variant="body2" component="p">
          {test.date}
        </Typography>
      </Grid>
      <Grid item xs={6}>
        <Button  onClick={()=> (plsPrint(test.id))} >Download</Button>
        {/* <Button> <a href=`/test/${test.id}` download></a>Download</Button> */}
        {/* console.log("yoooo"); */}
      </Grid>
    </Card>
  );
};

export default List;
