import React from "react";
import Link from "@mui/material/Link";
import Grid from "@mui/material/Grid";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import aiishPic from "../images/AIISH_LoGO.jpeg";
import iiitPic from "../images/IIITLoGO.jpeg";
import Container from "@mui/material/Container";
import CssBaseline from "@mui/material/CssBaseline";

const theme = createTheme();

export default function Home(){
    return (
    <ThemeProvider theme={theme}>
      <Grid container spacing={2}>
        <Grid item xs={4}>
          <Box
            display="flex"
            alignItems="center"
            justifyContent="center"
            sx={{
              marginTop: 4,
              height: "20vh",
              backgroundColor: "primary",
            }}
          >
            <img src={aiishPic} alt="AIISH" height="100vh" width="auto" />
          </Box>
        </Grid>
        <Grid item xs={4}>
          <Box
            sx={{
                marginTop: 20,
                display: "flex",
                flexDirection: "row",
            }}
          >
          <Grid container>
              <Grid item xs={6}>
                <Button
                    href = "/login"
                    variant = "contained"
                    color = "primary"
                >
                Login
                </Button>
              </Grid>
              <Grid item xs={6}>
                <Button
                    href = "/reports"
                    variant = "contained"
                    color = "primary"
                >
                View Reports
                </Button>
              </Grid>
          </Grid>
              
          </Box>
        </Grid>
        <Grid item xs={4}>
          <Box
            display="flex"
            alignItems="center"
            justifyContent="center"
            sx={{
              marginTop: 4,
              height: "20vh",
              backgroundColor: "primary",
            }}
          >
            <img src={iiitPic} alt="IIIT" height="100vh" width="auto" />
          </Box>
        </Grid>
      </Grid>
      <Container component="main" maxWidth="xs">
        <CssBaseline />
        <Box
          sx={{
            marginTop: 8,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
          }}
        >
          {/*  */}
        </Box>
      </Container>
    </ThemeProvider>
    );
}