"use client"

import { ChakraProvider } from "@chakra-ui/react"
import React, { type PropsWithChildren, useEffect } from "react"
import { system } from "../../theme"

export function CustomProvider(props: PropsWithChildren) {
  // Force dark mode
  useEffect(() => {
    // Remove light mode classes and add dark mode
    document.documentElement.classList.remove('chakra-ui-light')
    document.documentElement.classList.add('chakra-ui-dark')
    document.documentElement.style.colorScheme = 'dark'
    
    // Set data attributes for Chakra
    document.documentElement.setAttribute('data-theme', 'dark')
    document.documentElement.setAttribute('data-color-mode', 'dark')
  }, [])

  return (
    <ChakraProvider value={system} forcedTheme="dark">
      {props.children}
    </ChakraProvider>
  )
}
