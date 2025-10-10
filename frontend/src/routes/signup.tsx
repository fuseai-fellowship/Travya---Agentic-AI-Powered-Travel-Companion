import { Container, Flex, Image, Input, Text,Heading,Box,VStack } from "@chakra-ui/react"
import {
  Link as RouterLink,
  createFileRoute,
  redirect,
} from "@tanstack/react-router"
import { type SubmitHandler, useForm } from "react-hook-form"
import { FiLock, FiUser,FiMail } from "react-icons/fi"

import type { UserRegister } from "@/client"
import { Button } from "@/components/ui/button"
import { Field } from "@/components/ui/field"
import { InputGroup } from "@/components/ui/input-group"
import { PasswordInput } from "@/components/ui/password-input"
import useAuth, { isLoggedIn } from "@/hooks/useAuth"
import { confirmPasswordRules, emailPattern, passwordRules } from "@/utils"
import Logo from "/assets/images/fastapi-logo.svg"

export const Route = createFileRoute("/signup")({
  component: SignUp,
  beforeLoad: async () => {
    if (isLoggedIn()) {
      throw redirect({
        to: "/",
      })
    }
  },
})

interface UserRegisterForm extends UserRegister {
  confirm_password: string
}

function SignUp() {
  const { signUpMutation } = useAuth()
  const {
    register,
    handleSubmit,
    getValues,
    formState: { errors, isSubmitting },
  } = useForm<UserRegisterForm>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      email: "",
      full_name: "",
      password: "",
      confirm_password: "",
    },
  })

  const onSubmit: SubmitHandler<UserRegisterForm> = (data) => {
    signUpMutation.mutate(data)
  }

  return (
    <Flex 
      flexDir={{ base: "column", md: "row" }} 
      justify="center" 
      align="center"
      minH="100vh"
      bg="gray.50"
      p={4}
    >
      <Container
        as="form"
        onSubmit={handleSubmit(onSubmit)}
        maxW="md"
        w="100%"
        alignItems="stretch"
        justifyContent="center"
        gap={6}
        centerContent
        bg="white"
        p={8}
        borderRadius="xl"
        boxShadow="lg"
      >
        {/* Header Section */}
        <Box textAlign="center" mb={2}>
          <Image
            src={Logo}
            alt="FastAPI logo"
            height="auto"
            maxW="180px"
            mx="auto"
            mb={4}
          />
          <Heading as="h1" size="lg" color="gray.800" mb={2}>
            Create Your Account
          </Heading>
          <Text color="gray.600" fontSize="sm">
            Join us today and get started
          </Text>
        </Box>
  
        {/* Form Fields */}
        <VStack w="100%" gap={4}>
          {/* Full Name Field */}
          <Field
            invalid={!!errors.full_name}
            errorText={errors.full_name?.message}
          >
            <InputGroup w="100%" startElement={<FiUser color="gray.500" />}>
              <Input
                id="full_name"
                minLength={3}
                {...register("full_name", {
                  required: "Full Name is required",
                })}
                placeholder="Enter your full name"
                type="text"
                size="lg"
                focusRingColor="blue.500"
              />
            </InputGroup>
          </Field>
  
          {/* Email Field */}
          <Field invalid={!!errors.email} errorText={errors.email?.message}>
            <InputGroup w="100%" startElement={<FiMail color="gray.500" />}>
              <Input
                id="email"
                {...register("email", {
                  required: "Email is required",
                  pattern: emailPattern,
                })}
                placeholder="Enter your email"
                type="email"
                size="lg"
                focusRingColor="blue.500"
              />
            </InputGroup>
          </Field>
  
          {/* Password Field */}
          <PasswordInput
            type="password"
            startElement={<FiLock color="gray.500" />}
            {...register("password", passwordRules())}
            placeholder="Create a password"
            errors={errors}
            size="lg"
            focusRingColor="blue.500"
          />
  
          {/* Confirm Password Field */}
          <PasswordInput
            type="password"
            startElement={<FiLock color="gray.500" />}
            {...register("confirm_password", confirmPasswordRules(getValues))}
            placeholder="Confirm your password"
            errors={errors}
            size="lg"
            focusRingColor="blue.500"
          />
  
          {/* Submit Button */}
          <Button
            variant="solid"
            type="submit"
            loading={isSubmitting}
            size="lg"
            w="100%"
            colorScheme="blue"
            fontSize="md"
            fontWeight="semibold"
            py={3}
            mt={2}
          >
            {isSubmitting ? "Creating Account..." : "Create Account"}
          </Button>
        </VStack>
  
        {/* Login Redirect */}
        <Box textAlign="center" mt={2}>
          <Text color="gray.600" fontSize="sm">
            Already have an account?{" "}
            <RouterLink 
              to="/login" 
              className="main-link"
              style={{ fontWeight: '600' }}
            >
              Sign in here
            </RouterLink>
          </Text>
        </Box>
      </Container>
    </Flex>
  )
}

export default SignUp
