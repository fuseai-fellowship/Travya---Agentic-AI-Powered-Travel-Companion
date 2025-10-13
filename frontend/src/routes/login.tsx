import {
  Container,
  Image,
  Input,
  Text,
  Box,
  VStack,
  Heading,
} from "@chakra-ui/react";
import {
  Link as RouterLink,
  createFileRoute,
  redirect,
} from "@tanstack/react-router";
import { type SubmitHandler, useForm } from "react-hook-form";
import { FiLock, FiMail } from "react-icons/fi";

import type { Body_login_login_access_token as AccessToken } from "@/client";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { InputGroup } from "@/components/ui/input-group";
import { PasswordInput } from "@/components/ui/password-input";
import useAuth, { isLoggedIn } from "@/hooks/useAuth";
// import Logo from "/assets/images/fastapi-logo.svg";
import Logo from "/assets/images/travya-logo.png";
import { emailPattern, passwordRules } from "../utils";

export const Route = createFileRoute("/login")({
  component: Login,
  beforeLoad: async () => {
    if (isLoggedIn()) {
      throw redirect({
        to: "/dashboard",
      });
    }
  },
});

function Login() {
  const { loginMutation, error, resetError } = useAuth();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<AccessToken>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      username: "",
      password: "",
    },
  });

  const onSubmit: SubmitHandler<AccessToken> = async (data) => {
    if (isSubmitting) return;

    resetError();

    try {
      await loginMutation.mutateAsync(data);
    } catch {
      // error is handled by useAuth hook
    }
  };
  return (
    <Container
      as="form"
      onSubmit={handleSubmit(onSubmit)}
      h="100vh"
      maxW="sm"
      alignItems="stretch"
      justifyContent="center"
      gap={6}
      centerContent
      px={4}
    >
      {/* Logo Section */}
      <Box textAlign="center" mb={2}>
        <Image
          src={Logo}
          alt="FastAPI logo"
          height="auto"
          maxW="2xs"
          mx="auto"
          mb={3}
        />
        <Heading as="h1" size="lg" color="gray.700" mb={2}>
          Welcome Back
        </Heading>
        <Text color="gray.600" fontSize="sm">
          Sign in to your account to continue
        </Text>
      </Box>

      {/* Form Fields */}
      <VStack w="100%" gap={4}>
        <Field
          invalid={!!errors.username}
          errorText={
            errors.username?.message || (error ? "Invalid credentials" : "")
          }
        >
          <InputGroup w="100%" startElement={<FiMail color="gray.500" />}>
            <Input
              id="username"
              {...register("username", {
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

        <PasswordInput
          type="password"
          startElement={<FiLock color="gray.500" />}
          {...register("password", passwordRules())}
          placeholder="Enter your password"
          errors={errors}
          size="lg"
          focusRingColor="blue.500"
        />

        {/* Forgot Password Link */}
        <Box alignSelf="flex-end">
          <RouterLink
            to="/recover-password"
            className="main-link"
            style={{ fontSize: "0.875rem" }}
          >
            Forgot your password?
          </RouterLink>
        </Box>

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
        >
          {isSubmitting ? "Signing in..." : "Sign In"}
        </Button>
      </VStack>

      {/* Sign Up Section */}
      <Box textAlign="center" mt={4}>
        <Text color="gray.600" fontSize="sm">
          Don't have an account?{" "}
          <RouterLink
            to="/signup"
            className="main-link"
            style={{ fontWeight: "600" }}
          >
            Create account
          </RouterLink>
        </Text>
      </Box>
    </Container>
  );
}
