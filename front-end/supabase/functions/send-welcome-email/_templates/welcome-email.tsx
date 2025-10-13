
import {
  Body,
  Container,
  Head,
  Heading,
  Html,
  Link,
  Preview,
  Text,
} from 'npm:@react-email/components@0.0.22';
import * as React from 'npm:react@18.3.1';

interface WelcomeEmailProps {
  userEmail: string;
  confirmUrl: string;
}

export const WelcomeEmail = ({
  userEmail,
  confirmUrl,
}: WelcomeEmailProps) => (
  <Html>
    <Head />
    <Preview>Welcome to ContextPilot! Please verify your email address</Preview>
    <Body style={main}>
      <Container style={container}>
        <Heading style={h1}>Welcome to ContextPilot!</Heading>
        <Text style={text}>
          Thanks for signing up! We're excited to have you on board.
        </Text>
        <Text style={text}>
          To get started, please verify your email address by clicking the button below:
        </Text>
        <Link
          href={confirmUrl}
          target="_blank"
          style={{
            ...link,
            display: 'block',
            marginBottom: '16px',
            padding: '12px 24px',
            backgroundColor: '#059669',
            color: 'white',
            textDecoration: 'none',
            borderRadius: '6px',
            textAlign: 'center' as const,
          }}
        >
          Verify Email Address
        </Link>
        <Text style={text}>
          Or copy and paste this URL into your browser:
        </Text>
        <Text style={code}>{confirmUrl}</Text>
        <Text style={text}>
          Once verified, you'll be able to:
        </Text>
        <ul style={list}>
          <li>Create workspaces and projects</li>
          <li>Track progress with intelligent milestones</li>
          <li>Collaborate with your team</li>
          <li>Get AI-powered project guidance</li>
        </ul>
        <Text style={footer}>
          If you didn't create an account, you can safely ignore this email.
        </Text>
        <Text style={footer}>
          Best regards,<br />
          The ContextPilot Team
        </Text>
      </Container>
    </Body>
  </Html>
);

export default WelcomeEmail;

const main = {
  backgroundColor: '#ffffff',
  fontFamily:
    '-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Oxygen-Sans,Ubuntu,Cantarell,"Helvetica Neue",sans-serif',
};

const container = {
  margin: '0 auto',
  padding: '20px 0 48px',
  maxWidth: '560px',
};

const h1 = {
  color: '#333',
  fontSize: '24px',
  fontWeight: 'bold',
  margin: '40px 0',
  padding: '0',
};

const text = {
  color: '#333',
  fontSize: '16px',
  lineHeight: '26px',
  margin: '16px 0',
};

const link = {
  color: '#059669',
  textDecoration: 'underline',
};

const list = {
  color: '#333',
  fontSize: '16px',
  lineHeight: '26px',
  margin: '16px 0',
  paddingLeft: '20px',
};

const code = {
  display: 'inline-block',
  padding: '16px 4.5%',
  width: '90.5%',
  backgroundColor: '#f4f4f4',
  borderRadius: '5px',
  border: '1px solid #eee',
  color: '#333',
  fontSize: '14px',
  fontFamily: 'monospace',
  wordBreak: 'break-all' as const,
};

const footer = {
  color: '#898989',
  fontSize: '12px',
  lineHeight: '22px',
  marginTop: '12px',
  marginBottom: '24px',
};
