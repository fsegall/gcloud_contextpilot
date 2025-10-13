
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

interface InvitationEmailProps {
  inviterName: string;
  workspaceName: string;
  role: string;
  inviteUrl: string;
}

export const InvitationEmail = ({
  inviterName,
  workspaceName,
  role,
  inviteUrl,
}: InvitationEmailProps) => (
  <Html>
    <Head />
    <Preview>You've been invited to join {workspaceName} on ContextPilot</Preview>
    <Body style={main}>
      <Container style={container}>
        <Heading style={h1}>You're invited!</Heading>
        <Text style={text}>
          <strong>{inviterName}</strong> has invited you to join the workspace{' '}
          <strong>{workspaceName}</strong> on ContextPilot as a <strong>{role}</strong>.
        </Text>
        <Text style={text}>
          ContextPilot is an intelligent project guidance platform that helps teams 
          track progress, manage milestones, and collaborate effectively.
        </Text>
        <Link
          href={inviteUrl}
          target="_blank"
          style={{
            ...link,
            display: 'block',
            marginBottom: '16px',
            padding: '12px 24px',
            backgroundColor: '#2563eb',
            color: 'white',
            textDecoration: 'none',
            borderRadius: '6px',
            textAlign: 'center' as const,
          }}
        >
          Accept Invitation
        </Link>
        <Text style={text}>
          Or copy and paste this URL into your browser:
        </Text>
        <Text style={code}>{inviteUrl}</Text>
        <Text style={footer}>
          If you didn't expect this invitation, you can safely ignore this email.
        </Text>
        <Text style={footer}>
          Best regards,<br />
          The ContextPilot Team
        </Text>
      </Container>
    </Body>
  </Html>
);

export default InvitationEmail;

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
  color: '#2563eb',
  textDecoration: 'underline',
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
